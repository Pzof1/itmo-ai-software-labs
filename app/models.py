from datetime import UTC, datetime

from sqlalchemy import BIGINT, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.enums import TodoPriority, TodoStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BIGINT, unique=True, index=True, nullable=True)
    login: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]


class Tasks(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[TodoStatus] = mapped_column(String, default=TodoStatus.PENDING)
    description: Mapped[str | None]
    priority: Mapped[TodoPriority] = mapped_column(String, default=TodoPriority.LOW)
    due_date: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
