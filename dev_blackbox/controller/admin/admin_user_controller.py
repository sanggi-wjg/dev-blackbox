from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.admin.dto.user_dto import CreateUserRequestDto
from dev_blackbox.controller.api.dto.user_dto import UserResponseDto
from dev_blackbox.controller.security_config import (
    AuthToken,
    CurrentAdminUser,
)
from dev_blackbox.core.database import get_db
from dev_blackbox.service.user_service import UserService

router = APIRouter(prefix="/admin-api/v1/users", tags=["User Admin"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[UserResponseDto],
)
async def get_users(
    token: AuthToken,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    users = service.get_users()
    return users


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseDto,
)
async def create_user(
    request: CreateUserRequestDto,
    token: AuthToken,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.create_user(request)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_user(
    user_id: int,
    token: AuthToken,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    service.delete_user(user_id)
