from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.dto.github_user_secret_dto import (
    CreateGitHubSecretRequestDto,
    GitHubSecretResponseDto,
)
from dev_blackbox.core.database import get_db
from dev_blackbox.service.github_user_secret_service import GitHubUserSecretService

router = APIRouter(prefix="/github-secrets", tags=["GitHub Secret"])


@router.post(
    "",
    response_model=GitHubSecretResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_github_secret(
    request: CreateGitHubSecretRequestDto,
    db: Session = Depends(get_db),
):
    service = GitHubUserSecretService(db)
    secret = service.create_secret(request)
    response = GitHubSecretResponseDto.model_validate(secret)
    db.commit()
    return response


@router.get(
    "/users/{user_id}",
    response_model=GitHubSecretResponseDto,
)
async def get_github_secret_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = GitHubUserSecretService(db)
    secret = service.get_secret_by_user_id(user_id)
    response = GitHubSecretResponseDto.model_validate(secret)
    db.commit()
    return response
