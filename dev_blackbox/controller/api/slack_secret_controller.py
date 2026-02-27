from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.slack_secret_dto import SlackSecretSimpleResponseDto
from dev_blackbox.controller.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.slack_secret_service import SlackSecretService

router = APIRouter(prefix="/api/v1/slack-secrets", tags=["SlackSecret"])


@router.get(
    "",
    response_model=list[SlackSecretSimpleResponseDto],
)
async def get_slack_secrets(
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = SlackSecretService(db)
    secrets = service.get_secrets()
    return [SlackSecretSimpleResponseDto.from_entity(s) for s in secrets]
