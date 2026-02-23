from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.user_dto import (
    UserDetailResponseDto,
)
from dev_blackbox.controller.security_config import CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["User"])


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserDetailResponseDto,
)
async def get_user_me(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.get_user_by_id_or_throw(current_user.id)
    return user
