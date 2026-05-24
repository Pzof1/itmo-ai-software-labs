from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependency import get_current_user, get_db
from app.enums import TodoStatus
from app.models import User
from app.schemas import StatsResponse, TaskRequest, TaskResponse, TaskUpdateRequest
from app.service import tasks as tasks_service

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse, summary="Create new task", status_code=201)
def create_task(
    payload: TaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return tasks_service.create_task(db, current_user, payload)


@router.get("/tasks", response_model=list[TaskResponse], summary="Show list of all tasks")
def get_all_tasks(
    status: TodoStatus | None = None,
    sort_by_creation_date: bool = False,
    limit: Annotated[int, Query(le=100)] = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return tasks_service.get_all_tasks(
        db, current_user, status, sort_by_creation_date, limit, offset
    )


@router.delete("/tasks/{task_id}", summary="Delete task with id", status_code=204)
def delete_task_by_id(
    task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    return tasks_service.delete_task_by_id(db, current_user, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskResponse, summary="Update task with id")
def update_task_by_id(
    task_id: int,
    payload: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return tasks_service.update_task_by_id(db, current_user, task_id, payload)


@router.get("/tasks/stats", response_model=StatsResponse, summary="Gives tasks stats")
def get_tasks_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StatsResponse:
    return tasks_service.get_tasks_stats(db, current_user)


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Show task with id")
def get_task_by_id(
    task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> TaskResponse:
    return tasks_service.get_task_by_id(db, current_user, task_id)
