from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_user(
    db: Session, login: str, hashed_password: str, telegram_id: int | None = None
) -> User:
    user = User(login=login, hashed_password=hashed_password, telegram_id=telegram_id)
    db.add(user)
    db.flush()
    return user


def get_user_by_login(db: Session, login: str) -> User | None:
    stmt = select(User).where(User.login == login)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    return db.execute(stmt).scalar_one_or_none()
