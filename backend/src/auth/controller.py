from typing import Annotated, Any

from sqlalchemy.ext.asyncio import AsyncSession

from litestar import Controller, post, get, Request, Response
from litestar.di import Provide
from litestar.params import Body
from litestar.enums import RequestEncodingType
from litestar.security.jwt import Token

from src.auth.service import AuthService
from src.auth.schemas import UserRegister, UserLogin, AccessTokenResponse, UserResponse
from src.core.config import settings

from core.models.db_helper import get_db_session
from src.core.models import User


async def provide_auth_service(db_session: AsyncSession) -> AuthService:
    return AuthService(session=db_session)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set refresh token as httponly cookie."""
    max_age = settings.auth.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=settings.auth.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=settings.cookies.httponly,
        secure=settings.cookies.secure,
        samesite=settings.cookies.samesite,
        path="/api/v1/auth",  # Only send for auth endpoints
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(
        key=settings.auth.REFRESH_TOKEN_COOKIE_NAME,
        path="/api/v1/auth",
    )


class AuthController(Controller):
    path = "/auth"
    tags = ["Auth"]
    dependencies = {
        "auth_service": Provide(provide_auth_service),
        "db_session": Provide(get_db_session),
    }

    @post("/register")
    async def register(
        self, data: UserRegister, auth_service: AuthService
    ) -> UserResponse:
        created_user = await auth_service.register_user(data)
        return UserResponse.model_validate(created_user)

    @post("/login")
    async def login(
        self,
        data: Annotated[UserLogin, Body(media_type=RequestEncodingType.URL_ENCODED)],
        auth_service: AuthService,
    ) -> Response[AccessTokenResponse]:
        import traceback
        import sys
        try:
            tokens = await auth_service.login_user(data)
            
            response_data = AccessTokenResponse(
                access_token=tokens.access_token,
                token_type=tokens.token_type,
            )
            
            response = Response(content=response_data)
            set_refresh_cookie(response, tokens.refresh_token)
            
            return response
        except Exception:
            print("ERROR IN LOGIN ENDPOINT:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            raise

    @post("/refresh")
    async def refresh(
        self, request: Request, auth_service: AuthService
    ) -> Response[AccessTokenResponse]:
        # Get refresh token from httponly cookie
        refresh_token = request.cookies.get(settings.auth.REFRESH_TOKEN_COOKIE_NAME)
        
        tokens = await auth_service.refresh_tokens(refresh_token)
        
        response_data = AccessTokenResponse(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
        )
        
        response = Response(content=response_data)
        set_refresh_cookie(response, tokens.refresh_token)
        
        return response

    @post("/logout")
    async def logout(
        self, request: Request[User, Token, Any], auth_service: AuthService
    ) -> Response[None]:
        await auth_service.logout_user(request.user.id)
        
        response = Response(content=None, status_code=204)
        clear_refresh_cookie(response)
        
        return response

    @get("/me")
    async def get_me(self, request: Request[User, Token, Any]) -> UserResponse:
        return UserResponse.model_validate(request.user)
