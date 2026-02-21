from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.dto.user_dto import (
    CreateUserRequestDto,
    UserResponseDto,
    UserDetailResponseDto,
)
from dev_blackbox.core.database import get_db
from dev_blackbox.service.user_service import UserService

router = APIRouter(prefix="/users", tags=["User"])


@router.post(
    "",
    response_model=UserResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: CreateUserRequestDto,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.create_user(request)
    return user


@router.get(
    "/{user_id}",
    response_model=UserDetailResponseDto,
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.get_user(user_id)
    return user


@router.get(
    "",
    response_model=list[UserResponseDto],
)
async def get_users(
    db: Session = Depends(get_db),
):
    service = UserService(db)
    users = service.get_users()
    return users
