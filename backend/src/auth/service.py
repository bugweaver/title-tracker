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
            
            if sub is None:
                raise NotAuthorizedException(detail="Некорректный токен")
            
            # Verify it's actually a refresh token
            if token_type != "refresh":
                raise NotAuthorizedException(detail="Неверный тип токена")

            user_id = int(sub)

        except JWTError:
            raise NotAuthorizedException(detail="Недействительный токен")
        except ValueError:
            raise NotAuthorizedException(detail="Некорректный формат токена")

        # 2. Verify token exists in Redis (strict session check)
        redis_key = f"refresh_token:{user_id}"
        stored_token = await redis_client.get(redis_key)

        if not stored_token or stored_token != refresh_token:
            raise NotAuthorizedException(detail="Сессия истекла или отозвана")

        return await self._create_tokens(user_id)

    async def logout_user(self, user_id: int) -> None:
        """Logout user by removing their refresh token from Redis."""
        await redis_client.delete(f"refresh_token:{user_id}")

    async def _create_tokens(self, user_id: int) -> TokenInfo:
        """Create new access and refresh token pair."""
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

        # Store refresh token in Redis
        await redis_client.set(
            f"refresh_token:{user_id}",
            refresh_token,
            ex=timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return TokenInfo(access_token=access_token, refresh_token=refresh_token)
