from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.api.dto.slack_user_dto import (
    AssignSlackUserRequestDto,
    SlackUserResponseDto,
)
from dev_blackbox.controller.api.param.slack_user_param import SlackUserParam
from dev_blackbox.controller.config.security_config import CurrentUser, AuthToken
from dev_blackbox.core.database import get_db
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.service.slack_user_service import SlackUserService

router = APIRouter(prefix="/api/v1/slack-users", tags=["SlackUser"])


@router.get(
    "",
    response_model=list[SlackUserResponseDto],
)
async def get_slack_users(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[SlackUserParam, Query()],
    db: Session = Depends(get_db),
):
    service = SlackUserService(db)
    encrypt_service = get_encrypt_service()
    slack_users = service.get_slack_users(slack_secret_id=param.slack_secret_id)

    return [
        SlackUserResponseDto.from_entity(slack_user, encrypt_service) for slack_user in slack_users
    ]


@router.patch(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def assign_slack_user_to_user(
    request: AssignSlackUserRequestDto,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = SlackUserService(db)
    service.assign_user(
        current_user.id,
        request.slack_secret_id,
        request.slack_user_id,
    )


@router.delete(
    "/{slack_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def unassign_slack_user_from_user(
    slack_user_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = SlackUserService(db)
    service.unassign_user(
        current_user.id,
        slack_user_id,
    )
