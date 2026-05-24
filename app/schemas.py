from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import TodoPriority, TodoStatus


class UserRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=127)
    password: str = Field(..., min_length=8, max_length=20)

    @field_validator('login')
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("User name cannot be empty")
        return v


class UserTelegramRequest(BaseModel):
    telegram_id: int


class UserResponse(BaseModel):
    id: int
    login: str

    model_config = ConfigDict(from_attributes=True)


class TaskRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=127)
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.LOW
    due_date: datetime | None = None
    description: str | None = Field(None, max_length=1024)

    @field_validator('due_date')
    def due_date_in_future(cls, v: datetime | None):
        if v:
            target_date = v.astimezone(
                timezone.utc).replace(tzinfo=None).date()

            now_date = datetime.now(timezone.utc).replace(tzinfo=None).date()

            if target_date < now_date:
                raise ValueError("Due date cannot be in the past")
        return v


class TaskResponse(BaseModel):
    id: int
    name: str
    status: TodoStatus
    priority: TodoPriority
    description: str | None
    due_date: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TaskUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=127)
    status: TodoStatus | None = None
    priority: TodoPriority | None = None
    due_date: datetime | None = None
    description: str | None = Field(None, max_length=1024)

    @field_validator('due_date')
    def due_date_in_future(cls, v: datetime | None):
        if v:
            target_date = v.astimezone(
                timezone.utc).replace(tzinfo=None).date()

            now_date = datetime.now(timezone.utc).replace(tzinfo=None).date()

            if target_date < now_date:
                raise ValueError("Due date cannot be in the past")
        return v


class StatsResponse(BaseModel):
    completed_count: int
    total_tasks: int

    model_config = ConfigDict(from_attributes=True)
