from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.api.dto.slack_user_dto import SlackUserResponseDto
from dev_blackbox.controller.security_config import CurrentUser, AuthToken
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
    db: Session = Depends(get_db),
):
    service = SlackUserService(db)
    encrypt_service = get_encrypt_service()
    slack_users = service.get_slack_users()

    return [
        SlackUserResponseDto(
            id=slack_user.id,
            member_id=slack_user.member_id,
            is_active=slack_user.is_active,
            display_name=encrypt_service.decrypt(slack_user.display_name),
            real_name=encrypt_service.decrypt(slack_user.real_name),
            email=encrypt_service.decrypt(slack_user.email) if slack_user.email else None,
            user_id=slack_user.user_id,
            created_at=slack_user.created_at,
            updated_at=slack_user.updated_at,
        )
        for slack_user in slack_users
    ]


@router.patch(
    "/{slack_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def assign_slack_user_to_user(
    slack_user_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = SlackUserService(db)
    service.assign_user(
        current_user.id,
        slack_user_id,
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
