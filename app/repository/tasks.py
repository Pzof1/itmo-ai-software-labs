from collections.abc import Sequence
from typing import Any

from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.enums import TodoStatus
from app.models import Tasks
from app.schemas import TaskRequest


def create_task(db: Session, user_id: int, task_data: TaskRequest) -> Tasks:

    task = Tasks(owner_id=user_id, **task_data.model_dump(exclude_unset=True))

    db.add(task)
    db.flush()
    return task


def get_all_tasks(
    db: Session,
    user_id: int,
    sort_by_creation_date: bool,
    status: TodoStatus | None,
    limit: int,
    offset: int,
) -> Sequence[Tasks]:
    """Fetch all tasks for a specific user from the database.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user iwning the tasks..
        sort_by_creation_date (bool): If true, sorts tasks by creation date (descending).
        status (TodoStatus | None): If provided, filters tasks by their status.
        limit (int): Maximum number of tasks to return (for pagination).
        offset (int): Number of tasks to skip (for pagination).

    Returns:
        List[Tasks]: A list of task model instances.
    """
    stmt = select(Tasks).where(Tasks.owner_id == user_id, Tasks.is_deleted.is_(False))

    if status == TodoStatus.ACTIVE:
        stmt = stmt.where(Tasks.status != TodoStatus.DONE)

    elif status:
        stmt = stmt.where(Tasks.status == status)

    if sort_by_creation_date:
        stmt = stmt.order_by(desc(Tasks.created_at))

    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


def delete_task_by_id(db: Session, user_id: int, task_id: int) -> int:
    stmt = (
        update(Tasks)
        .where(Tasks.owner_id == user_id, Tasks.id == task_id, Tasks.is_deleted.is_(False))
        .values(is_deleted=True)
    )
    result = db.execute(stmt)
    return result.rowcount  # type: ignore


def restore_task_by_id(db: Session, user_id: int, task_id: int) -> int:
    stmt = (
        update(Tasks)
        .where(Tasks.owner_id == user_id, Tasks.id == task_id, Tasks.is_deleted.is_(True))
        .values(is_deleted=False)
    )
    return db.execute(stmt).rowcount  # type: ignore


def update_task_by_id(db: Session, user_id: int, task_id: int, update_data: dict[str, Any]) -> int:
    stmt = (
        update(Tasks)
        .where(Tasks.owner_id == user_id)
        .where(Tasks.id == task_id)
        .where(Tasks.is_deleted.is_(False))
        .values(**update_data)
    )
    return db.execute(stmt).rowcount  # type: ignore


def get_task_by_id(db: Session, user_id: int, task_id: int) -> Tasks | None:
    stmt = select(Tasks).where(
        Tasks.owner_id == user_id, Tasks.id == task_id, Tasks.is_deleted.is_(False)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_tasks_count(db: Session, user_id: int, status: TodoStatus | None = None) -> int | None:
    """Count tasks. If status selcted count with status filter."""
    stmt = select(func.count(Tasks.id)).where(
        Tasks.owner_id == user_id, Tasks.is_deleted.is_(False)
    )

    if status:
        stmt = stmt.where(Tasks.status == status)

    return db.execute(stmt).scalar() or 0
