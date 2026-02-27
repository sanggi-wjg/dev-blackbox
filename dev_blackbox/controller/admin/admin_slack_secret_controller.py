from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.admin.dto.slack_secret_dto import (
    CreateSlackSecretRequestDto,
    SlackSecretResponseDto,
)
from dev_blackbox.controller.security_config import CurrentAdminUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.slack_secret_service import SlackSecretService
from dev_blackbox.service.slack_user_service import SlackUserService

router = APIRouter(prefix="/admin-api/v1/slack-secrets", tags=["Admin Slack Secret Management"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SlackSecretResponseDto,
)
async def create_slack_secret(
    request: CreateSlackSecretRequestDto,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = SlackSecretService(db)
    secret = service.create_secret(
        name=request.name,
        bot_token=request.bot_token,
    )
    return SlackSecretResponseDto.from_entity(secret)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[SlackSecretResponseDto],
)
async def get_slack_secrets(
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = SlackSecretService(db)
    secrets = service.get_secrets()
    return [SlackSecretResponseDto.from_entity(s) for s in secrets]


@router.delete(
    "/{slack_secret_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_slack_secret(
    slack_secret_id: int,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = SlackSecretService(db)
    service.delete_secret(slack_secret_id)


@router.post(
    "/{slack_secret_id}/sync",
    status_code=status.HTTP_200_OK,
    response_model=None,
)
async def sync_slack_users(
    slack_secret_id: int,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    slack_user_service = SlackUserService(db)
    slack_user_service.sync_slack_users(slack_secret_id=slack_secret_id)
