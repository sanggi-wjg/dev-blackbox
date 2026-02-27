from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.github_user_secret_dto import (
    CreateGitHubSecretRequestDto,
    GitHubSecretResponseDto,
)
from dev_blackbox.controller.security_config import CurrentUser, AuthToken
from dev_blackbox.core.database import get_db
from dev_blackbox.service.github_user_secret_service import GitHubUserSecretService

router = APIRouter(prefix="/api/v1/github-secrets", tags=["GitHub Secret"])


@router.post(
    "",
    response_model=GitHubSecretResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_github_secret(
    request: CreateGitHubSecretRequestDto,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = GitHubUserSecretService(db)
    user_secret = service.create_secret(current_user.id, request)
    return GitHubSecretResponseDto.from_entity(user_secret)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_github_secret_by_user_id(
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = GitHubUserSecretService(db)
    service.delete_secret(current_user.id)
    return None
