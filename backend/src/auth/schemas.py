from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
import re


class UserRegister(BaseModel):
    email: EmailStr
    login: str
    password: str
    name: str | None = None

    @field_validator('login')
    @classmethod
    def validate_login(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Логин должен содержать минимум 3 символа')
        if len(v) > 50:
            raise ValueError('Логин слишком длинный')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Логин может содержать только буквы, цифры и _')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class TokenInfo(BaseModel):
    """Full token info (internal use, includes refresh_token)."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Response for login/refresh (refresh_token goes in httponly cookie)."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    login: str
    login: str
    name: str | None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
