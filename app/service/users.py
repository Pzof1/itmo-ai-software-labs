import secrets

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.repository import users as users_repository
from app.schemas import TokenResponse, UserResponse, UserTelegramRequest


def create_user(
    db: Session, login: str, password: str, telegram_id: int | None = None
) -> UserResponse:
    if users_repository.get_user_by_login(db, login) is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = hash_password(password)
    user = users_repository.create_user(db, login, hashed_password, telegram_id)
    db.commit()
    return UserResponse.model_validate(user)


def authenticate_user(db: Session, login: str, password: str) -> TokenResponse:
    """Authenticate a user and return a JWT access token.

    Args:
        db (Session): Database session.
        login (str): User login.
        password (str): User plain-text password.

    Raises:
        HTTPException: If the login or password does not match.

    Returns:
        TokenResponse: Object containing the access token and its type.
    """
    user = users_repository.get_user_by_login(db, login)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect login or password")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect login or password")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


def authenticate_user_via_telegram(db: Session, payload: UserTelegramRequest) -> TokenResponse:
    """Authenticate a user using their Telegram ID.

    Args:
        db (Session): Database session.
        payload (UserTelegramRequest): Schema containing telegram_id.

    Returns:
        TokenResponse: Object containing the access token and its type.
    """
    user = users_repository.get_user_by_telegram_id(db, payload.telegram_id)

    if user is None:
        try:
            telegram_id = payload.telegram_id
            username = f"tg_{telegram_id}"
            random_password = secrets.token_urlsafe(16)
            user = create_user(
                db, login=username, password=random_password, telegram_id=telegram_id
            )
        except IntegrityError:
            db.rollback()
            user = users_repository.get_user_by_telegram_id(db, payload.telegram_id)
            if user is None:
                raise HTTPException(status_code=500, detail="Database sync error")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)
