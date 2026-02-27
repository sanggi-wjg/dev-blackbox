from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret


class CreateJiraSecretRequestDto(BaseModel):
    name: str
    url: str
    username: str
    api_token: str


class JiraSecretResponseDto(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: JiraSecret) -> JiraSecretResponseDto:
        return cls(
            id=entity.id,
            name=entity.name,
            url=entity.url,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class SyncJiraUsersRequestDto(BaseModel):
    project: str
