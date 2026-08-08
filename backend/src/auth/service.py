import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import HTTPException, NotAuthorizedException

from src.core.models import User
from src.core.security import get_password_hash, verify_password, validate_password
from src.core.config import settings
from core.redis.client import redis_client
from src.auth.schemas import UserRegister, UserLogin, TokenInfo


def _session_redis_key(user_id: int, jti: str) -> str:
    """Per-device refresh session key (supports multiple concurrent logins)."""
    return f"refresh_token:{user_id}:{jti}"


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, data: UserRegister) -> User:
        # Validate password strength
        validate_password(data.password)
        
        # Check for existing user
        stmt = select(User).where(
            (User.email == data.email) | (User.login == data.login)
        )
        existing = await self.session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(detail="Пользователь уже существует", status_code=400)

        # Create user
        new_user = User(
            email=data.email,
            login=data.login,
            password=get_password_hash(data.password),
            name=data.name,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def login_user(self, data: UserLogin) -> TokenInfo:
        # Find user by login or email
        stmt = select(User).where(
            (User.login == data.username) | (User.email == data.username)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password):
            raise NotAuthorizedException(detail="Неверный логин или пароль")

        return await self._create_tokens(user.id)

    async def refresh_tokens(self, refresh_token: str) -> TokenInfo:
        """Refresh tokens. Validates the refresh token and issues new pair."""
        if not refresh_token:
            raise NotAuthorizedException(detail="Refresh token не предоставлен")
        
        # 1. Verify JWT signature
        try:
            payload = jwt.decode(
                refresh_token,
                settings.auth.JWT_SECRET,
                algorithms=[settings.auth.ALGORITHM],
            )

            sub = payload.get("sub")
            token_type = payload.get("type")
            jti = payload.get("jti")
            
            if sub is None:
                raise NotAuthorizedException(detail="Некорректный токен")
            
            # Verify it's actually a refresh token
            if token_type != "refresh":
                raise NotAuthorizedException(detail="Неверный тип токена")

            if not jti:
                raise NotAuthorizedException(detail="Некорректный токен")

            user_id = int(sub)

        except JWTError:
            raise NotAuthorizedException(detail="Недействительный токен")
        except ValueError:
            raise NotAuthorizedException(detail="Некорректный формат токена")

        # 2. Verify this device session exists in Redis
        redis_key = _session_redis_key(user_id, jti)
        if not await redis_client.exists(redis_key):
            raise NotAuthorizedException(detail="Сессия истекла или отозвана")

        # Rotate: revoke the used refresh token, then issue a new session
        await redis_client.delete(redis_key)
        return await self._create_tokens(user_id)

    async def logout_user(self, user_id: int, refresh_token: str | None = None) -> None:
        """Logout only the current device session (identified by refresh cookie)."""
        if not refresh_token:
            return

        try:
            payload = jwt.decode(
                refresh_token,
                settings.auth.JWT_SECRET,
                algorithms=[settings.auth.ALGORITHM],
            )
            if payload.get("type") != "refresh":
                return

            sub = payload.get("sub")
            jti = payload.get("jti")
            if not sub or not jti or int(sub) != user_id:
                return

            await redis_client.delete(_session_redis_key(user_id, jti))
        except (JWTError, ValueError):
            # Cookie already invalid/expired — nothing to revoke
            return

    async def _create_tokens(self, user_id: int) -> TokenInfo:
        """Create new access and refresh token pair for a new device session."""
        now = datetime.now(timezone.utc)

        # Access Token (short-lived)
        access_payload = {
            "sub": str(user_id),
            "exp": now + timedelta(minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": now,
            "type": "access",
        }
        access_token = jwt.encode(
            access_payload, settings.auth.JWT_SECRET, algorithm=settings.auth.ALGORITHM
        )

        # Refresh Token (long-lived)
        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            "sub": str(user_id),
            "exp": now + timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": now,
            "jti": refresh_jti,
            "type": "refresh",
        }
        refresh_token = jwt.encode(
            refresh_payload, settings.auth.JWT_SECRET, algorithm=settings.auth.ALGORITHM
        )

        # Store this session in Redis (does not invalidate other devices)
        await redis_client.set(
            _session_redis_key(user_id, refresh_jti),
            "1",
            ex=timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return TokenInfo(access_token=access_token, refresh_token=refresh_token)
