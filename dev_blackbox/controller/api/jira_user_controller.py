from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.jira_user_dto import (
    JiraUserResponseDto,
    AssignJiraUserRequestDto,
)
from dev_blackbox.controller.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.service.jira_user_service import JiraUserService

router = APIRouter(prefix="/api/v1/jira-users", tags=["JiraUser"])


@router.get(
    "",
    response_model=list[JiraUserResponseDto],
)
async def get_jira_users(
    token: AuthToken,
    current_user: CurrentUser,
    jira_secret_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = JiraUserService(db)
    encrypt_service = get_encrypt_service()
    jira_users = service.get_jira_users(jira_secret_id)

    return [
        JiraUserResponseDto(
            id=jira_user.id,
            jira_secret_id=jira_user.jira_secret_id,
            account_id=jira_user.account_id,
            active=jira_user.active,
            display_name=encrypt_service.decrypt(jira_user.display_name),
            email_address=encrypt_service.decrypt(jira_user.email_address),
            url=jira_user.url,
            project=jira_user.project,
            user_id=jira_user.user_id,
            created_at=jira_user.created_at,
            updated_at=jira_user.updated_at,
        )
        for jira_user in jira_users
    ]


@router.patch(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def assign_jira_user(
    token: AuthToken,
    current_user: CurrentUser,
    request: AssignJiraUserRequestDto,
    db: Session = Depends(get_db),
):
    service = JiraUserService(db)
    service.assign_user(
        user_id=current_user.id,
        jira_secret_id=request.jira_secret_id,
        jira_user_id=request.jira_user_id,
        project=request.project,
    )


@router.delete(
    "/{jira_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def unassign_jira_user(
    jira_user_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = JiraUserService(db)
    service.unassign_user(
        user_id=current_user.id,
        jira_user_id=jira_user_id,
    )
