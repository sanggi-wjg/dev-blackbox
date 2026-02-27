from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret


class JiraSecretSimpleResponseDto(BaseModel):
    id: int
    name: str
    url: str

    @classmethod
    def from_entity(cls, entity: JiraSecret) -> JiraSecretSimpleResponseDto:
        return cls(
            id=entity.id,
            name=entity.name,
            url=entity.url,
        )
