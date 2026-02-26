from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.service.model.github_user_secret_model import GitHubUserSecretModel
from dev_blackbox.service.model.jira_user_model import JiraUserModel
from dev_blackbox.service.model.slack_user_model import SlackUserModel

if TYPE_CHECKING:
    from dev_blackbox.core.encrypt import EncryptService
    from dev_blackbox.storage.rds.entity.user import User


class UserModel(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UserDetailModel(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    created_at: datetime
    updated_at: datetime
    github_user_secret: GitHubUserSecretModel | None = None
    jira_user: JiraUserModel | None = None
    slack_user: SlackUserModel | None = None

    @classmethod
    def from_entity(cls, user: User, encrypt_service: EncryptService) -> UserDetailModel:
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            timezone=user.timezone,
            tz_info=user.tz_info,
            created_at=user.created_at,
            updated_at=user.updated_at,
            github_user_secret=(
                GitHubUserSecretModel.from_entity(user.github_user_secret, encrypt_service)
                if user.github_user_secret
                else None
            ),
            jira_user=(
                JiraUserModel.from_entity(user.jira_user, encrypt_service)
                if user.jira_user
                else None
            ),
            slack_user=(
                SlackUserModel.from_entity(user.slack_user, encrypt_service)
                if user.slack_user
                else None
            ),
        )
