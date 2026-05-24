from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependency import get_db, validate_internal_secret
from app.schemas import TokenResponse, UserRequest, UserResponse, UserTelegramRequest
from app.service import users as users_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def create_user(payload: UserRequest, db: Session = Depends(get_db)):
    return users_service.create_user(db, payload.login, payload.password)


@router.post("/login", response_model=TokenResponse)
def login_user(payload: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return users_service.authenticate_user(db, payload.username, payload.password)


@router.post("/login/telegram", response_model=TokenResponse)
def login_via_telegram(
    payload: UserTelegramRequest, db: Session = Depends(get_db), _=Depends(validate_internal_secret)
):
    return users_service.authenticate_user_via_telegram(db, payload)
