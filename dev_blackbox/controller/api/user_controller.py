from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.github_user_secret_dto import GitHubSecretResponseDto
from dev_blackbox.controller.api.dto.jira_user_dto import JiraUserResponseDto
from dev_blackbox.controller.api.dto.slack_user_dto import SlackUserResponseDto
from dev_blackbox.controller.api.dto.user_dto import (
    UserDetailResponseDto,
)
from dev_blackbox.controller.config.security_config import CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.core.encrypt import get_encrypt_service
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
    encrypt_service = get_encrypt_service()
    user = service.get_user_by_id_or_throw(current_user.id)
    return UserDetailResponseDto(
        id=user.id,
        name=user.name,
        email=user.email,
        timezone=user.timezone,
        tz_info=user.tz_info,
        created_at=user.created_at,
        updated_at=user.updated_at,
        github_user_secret=(
            GitHubSecretResponseDto.from_entity(user.github_user_secret, encrypt_service)
            if user.github_user_secret
            else None
        ),
        jira_user=(
            JiraUserResponseDto.from_entity(user.jira_user, encrypt_service)
            if user.jira_user
            else None
        ),
        slack_user=(
            SlackUserResponseDto.from_entity(user.slack_user, encrypt_service)
            if user.slack_user
            else None
        ),
    )
