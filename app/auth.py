from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from .config import settings


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The hashed password.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password.

    Args:
        password (str): The plain-text password to check.
        hashed_password (str): The hashed password from the database.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(payload: dict) -> str:
    """Generate a new JWT access token.

    Args:
        payload (dict): Dictionary containing data (claims) to include in the token.

    Returns:
        str: JWT token.
    """
    data = payload.copy()
    exp_time = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE)
    data["exp"] = exp_time
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token
