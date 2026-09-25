from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.enums import TodoStatus
from app.models import User
from app.repository import tasks as tasks_repository
from app.schemas import StatsResponse, TaskRequest, TaskResponse, TaskUpdateRequest


def create_task(db: Session, current_user: User, task_data: TaskRequest) -> TaskResponse:
    task = tasks_repository.create_task(db, current_user.id, task_data)
    db.commit()
    return TaskResponse.model_validate(task)


def get_all_tasks(
    db: Session,
    current_user: User,
    status: TodoStatus | None,
    sort_by_creation_date: bool,
    limit: int,
    offset: int,
) -> list[TaskResponse]:
    """Retrieve and validate a list of tasks for the current user.

    Args:
        db (Session): Database session.
        current_user (User): The authenticated user object.
        status (TodoStatus | None): Optional status filter.
        sort_by_creation_date (bool): Flag to enable date sorting.
        limit (int): Pagination limit.
        offset (int): Pagination offset.

    Returns:
        list[TaskResponse]: Validated list of tasks ready for API response.
    """
    tasks = tasks_repository.get_all_tasks(
        db, current_user.id, sort_by_creation_date, status, limit, offset
    )
    return [TaskResponse.model_validate(task) for task in tasks]


def get_deleted_tasks(
    db: Session, current_user: User, limit: int, offset: int
) -> list[TaskResponse]:
    tasks = tasks_repository.get_deleted_tasks(db, current_user.id, limit, offset)
    return [TaskResponse.model_validate(task) for task in tasks]


def delete_task_by_id(db: Session, current_user: User, task_id: int) -> None:
    """Delete task by given id.

    Args:
        db (Session): Database session.
        current_user (User): The authenticated user object.
        task_id (int): Task id to be deleted.

    Raises:
        HTTPException: If the task is not found or does not belong to the user.

    Returns:
        None
    """
    result = tasks_repository.delete_task_by_id(db, current_user.id, task_id)

    if result == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    db.commit()


def restore_task_by_id(db: Session, current_user: User, task_id: int) -> TaskResponse:
    rowcount = tasks_repository.restore_task_by_id(db, current_user.id, task_id)
    if rowcount == 0:
        task = tasks_repository.get_task_by_id(db, current_user.id, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        raise HTTPException(status_code=409, detail=f"Task {task_id} is already active")
    db.commit()
    task = tasks_repository.get_task_by_id(db, current_user.id, task_id)
    return TaskResponse.model_validate(task)


def update_task_by_id(
    db: Session, current_user: User, task_id: int, payload: TaskUpdateRequest
) -> TaskResponse:
    """Update task by given id.

    Args:
        db (Session): Database session.
        current_user (User): The authenticated user object.
        task_id (int): ID of the task to update.
        payload (TaskUpdateRequest): Pydantic model containing fields to update.

    Raises:
        HTTPException: If the task is not found or does not update.

    Returns:
        TaskResponse: The updated task data as a validated schema.

    """
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        task = tasks_repository.get_task_by_id(db, current_user.id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return TaskResponse.model_validate(task)
    rowcount = tasks_repository.update_task_by_id(db, current_user.id, task_id, update_data)
    if rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    db.commit()
    updated_task = tasks_repository.get_task_by_id(db, current_user.id, task_id)
    return TaskResponse.model_validate(updated_task)


def get_task_by_id(db: Session, current_user: User, task_id: int) -> TaskResponse:
    task = tasks_repository.get_task_by_id(db, current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return TaskResponse.model_validate(task)


def get_tasks_stats(db: Session, current_user: User) -> StatsResponse:
    """Validate tasks count from db to pydantic model."""
    done_tasks = tasks_repository.get_tasks_count(db, current_user.id, status=TodoStatus.DONE)

    all_tasks = tasks_repository.get_tasks_count(db, current_user.id)

    data = {"completed_count": done_tasks, "total_tasks": all_tasks}

    return StatsResponse.model_validate(data)
