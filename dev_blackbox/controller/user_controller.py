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
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseDto,
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
    status_code=status.HTTP_200_OK,
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
    status_code=status.HTTP_200_OK,
    response_model=list[UserResponseDto],
)
async def get_users(
    db: Session = Depends(get_db),
):
    service = UserService(db)
    users = service.get_users()
    return users


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    service.delete_user(user_id)
