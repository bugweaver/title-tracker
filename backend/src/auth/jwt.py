from litestar.security.jwt import JWTAuth, Token
from sqlalchemy import select
from src.core.models import User
from core.models.db_helper import db_helper
from src.core.config import settings


async def retrieve_user_handler(token: Token, connection) -> User | None:
    """Вызывается автоматически при каждом запросе с токеном"""
    async with db_helper.session_factory() as session:
        # Получаем ID пользователя из поля 'sub' токена
        stmt = select(User).where(User.id == int(token.sub))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


jwt_config = JWTAuth[User](
    token_secret=settings.auth.JWT_SECRET,
    retrieve_user_handler=retrieve_user_handler,
    auth_header="Authorization",
    # Исключаем пути аутентификации из проверки
    exclude=[
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/schema",
    ],
)
