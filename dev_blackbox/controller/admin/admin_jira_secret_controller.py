from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.admin.dto.jira_secret_dto import (
    CreateJiraSecretRequestDto,
    JiraSecretResponseDto,
    SyncJiraUsersRequestDto,
)
from dev_blackbox.controller.security_config import CurrentAdminUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.jira_secret_service import JiraSecretService
from dev_blackbox.service.jira_user_service import JiraUserService

router = APIRouter(prefix="/admin-api/v1/jira-secrets", tags=["Admin Jira Secret Management"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=JiraSecretResponseDto,
)
async def create_jira_secret(
    request: CreateJiraSecretRequestDto,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = JiraSecretService(db)
    return service.create_secret(
        name=request.name,
        url=request.url,
        username=request.username,
        api_token=request.api_token,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[JiraSecretResponseDto],
)
async def get_jira_secrets(
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = JiraSecretService(db)
    return service.get_secrets()


@router.delete(
    "/{jira_secret_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_jira_secret(
    jira_secret_id: int,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    service = JiraSecretService(db)
    service.delete_secret(jira_secret_id)


@router.post(
    "/{jira_secret_id}/sync",
    status_code=status.HTTP_200_OK,
    response_model=None,
)
async def sync_jira_users(
    jira_secret_id: int,
    request: SyncJiraUsersRequestDto,
    current_admin_user: CurrentAdminUser,
    db: Session = Depends(get_db),
):
    jira_user_service = JiraUserService(db)
    jira_user_service.sync_jira_users(
        jira_secret_id=jira_secret_id,
        project=request.project,
    )
