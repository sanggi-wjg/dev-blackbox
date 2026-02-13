from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.dto.user_dto import CreateUserRequestDto, UserResponseDto
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
    response = UserResponseDto.model_validate(user)
    db.commit()
    return response


@router.get(
    "/{user_id}",
    response_model=UserResponseDto,
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.get_user(user_id)
    response = UserResponseDto.model_validate(user)
    db.commit()
    return response


@router.get(
    "",
    response_model=list[UserResponseDto],
)
async def get_users(
    db: Session = Depends(get_db),
):
    service = UserService(db)
    users = service.get_users()
    response = [UserResponseDto.model_validate(user) for user in users]
    db.commit()
    return response
