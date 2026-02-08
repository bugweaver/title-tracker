import re
import secrets
import bcrypt
from litestar.exceptions import HTTPException

# Password requirements
MIN_PASSWORD_LENGTH = 8
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d).+$')


class PasswordValidationError(HTTPException):
    """Exception raised when password doesn't meet requirements."""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=400)


def validate_password(password: str) -> None:
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one letter
    - At least one digit
    
    Raises PasswordValidationError if validation fails.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"Пароль должен содержать минимум {MIN_PASSWORD_LENGTH} символов"
        )
    
    if not PASSWORD_PATTERN.match(password):
        raise PasswordValidationError(
            "Пароль должен содержать буквы и цифры"
        )


def _truncate_password(password: str) -> bytes:
    """
    Truncates the password to 71 bytes to satisfy bcrypt limits.
    Returns bytes to avoid re-encoding issues.
    """
    return password.encode("utf-8")[:71]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt."""
    password_bytes = _truncate_password(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = _truncate_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)
