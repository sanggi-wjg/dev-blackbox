from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.token_dto import TokenResponseDto
from dev_blackbox.core.database import get_db
from dev_blackbox.service.user_service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponseDto,
    summary="토큰 로그인",
)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user_service = UserService(db)
    user = user_service.authenticate(form_data.username, form_data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = user_service.create_jwt_token(user)
    return TokenResponseDto(access_token=token)
