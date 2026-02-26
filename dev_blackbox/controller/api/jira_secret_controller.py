from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.jira_secret_dto import JiraSecretSimpleResponseDto
from dev_blackbox.controller.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.jira_secret_service import JiraSecretService

router = APIRouter(prefix="/api/v1/jira-secrets", tags=["JiraSecret"])


@router.get(
    "",
    response_model=list[JiraSecretSimpleResponseDto],
)
async def get_jira_secrets(
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = JiraSecretService(db)
    secrets = service.get_secrets()
    return secrets
