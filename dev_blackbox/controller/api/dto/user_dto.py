from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.controller.api.dto.github_user_secret_dto import GitHubSecretResponseDto
from dev_blackbox.controller.api.dto.jira_user_dto import JiraUserResponseDto
from dev_blackbox.controller.api.dto.slack_user_dto import SlackUserResponseDto

if TYPE_CHECKING:
    from dev_blackbox.core.encrypt import EncryptService
    from dev_blackbox.storage.rds.entity.user import User


class UserResponseDto(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: User) -> UserResponseDto:
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            timezone=entity.timezone,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class UserDetailResponseDto(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    created_at: datetime
    updated_at: datetime
    github_user_secret: GitHubSecretResponseDto | None
    jira_user: JiraUserResponseDto | None
    slack_user: SlackUserResponseDto | None

    @classmethod
    def from_entity(cls, entity: User, encrypt_service: EncryptService) -> UserDetailResponseDto:
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            timezone=entity.timezone,
            tz_info=entity.tz_info,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            github_user_secret=(
                GitHubSecretResponseDto.from_entity(entity.github_user_secret, encrypt_service)
                if entity.github_user_secret
                else None
            ),
            jira_user=(
                JiraUserResponseDto.from_entity(entity.jira_user, encrypt_service)
                if entity.jira_user
                else None
            ),
            slack_user=(
                SlackUserResponseDto.from_entity(entity.slack_user, encrypt_service)
                if entity.slack_user
                else None
            ),
        )
