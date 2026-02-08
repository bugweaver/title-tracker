import logging
from typing import Literal

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    log_format: str = LOG_DEFAULT_FORMAT

    @property
    def log_level_value(self) -> int:
        return logging.getLevelNamesMapping()[self.log_level.upper()]


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    auth: str = "/auth"
    users: str = "/users"
    etalons: str = "/etalons"
    change_requests: str = "/change-requests"
    change_review: str = "/change-review"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    decode_responses: bool = True
    socket_connect_timeout: int = 5
    socket_timeout: int = 5
    max_connections: int = 20

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class CookieConfig(BaseModel):
    httponly: bool
    secure: bool
    samesite: Literal["lax", "strict", "none"] | None

class AuthConfig(BaseModel):
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str | None

    # Twitch / IGDB API
    TWITCH_CLIENT_ID: str | None = None
    TWITCH_CLIENT_SECRET: str | None = None
    
    # TMDB API
    TMDB_API_KEY: str | None = None
    TMDB_READ_ACCESS_TOKEN: str | None = None

    COOKIE_HTTPONLY: bool = True
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] | None = "lax"

    JWT_SECRET: str = "dev-only-secret-key-change-in-production"

    run: RunConfig = RunConfig()
    logging: LoggingConfig = LoggingConfig()
    api: ApiPrefix = ApiPrefix()

    @property
    def auth(self) -> AuthConfig:
        return AuthConfig(JWT_SECRET=self.JWT_SECRET)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def db(self) -> DatabaseConfig:
        db_url_str = (
            "postgresql+asyncpg://"
            f"{self.POSTGRES_USER}"
            f":{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}"
            f":{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )
        return DatabaseConfig(url=PostgresDsn(db_url_str))

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            db=self.REDIS_DB,
            password=self.REDIS_PASSWORD,
        )

    @property
    def cookies(self) -> CookieConfig:
        return CookieConfig(
            httponly=self.COOKIE_HTTPONLY,
            secure=self.COOKIE_SECURE,
            samesite=self.COOKIE_SAMESITE,
        )


settings = Settings()  # type: ignore
