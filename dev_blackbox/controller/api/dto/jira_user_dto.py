from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.service.model.jira_user_model import JiraUserModel


class JiraUserResponseDto(BaseModel):
    id: int
    jira_secret_id: int
    account_id: str
    is_active: bool
    display_name: str
    email_address: str
    url: str
    project: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: JiraUserModel) -> JiraUserResponseDto:
        return cls(
            id=model.id,
            jira_secret_id=model.jira_secret_id,
            account_id=model.account_id,
            is_active=model.is_active,
            display_name=model.display_name,
            email_address=model.email_address,
            url=model.url,
            project=model.project,
            user_id=model.user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class AssignJiraUserRequestDto(BaseModel):
    jira_secret_id: int
    jira_user_id: int
    project: str
