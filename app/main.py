from fastapi import FastAPI

from app.api.v1.tasks import router as tasks_router
from app.api.v1.users import router as users_router

app = FastAPI(
    title="Todo API",
    description="Simple Todo application built with FastAPI",
    version="1.0.0",
    openapi_url="/openapi.json",
)

app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
