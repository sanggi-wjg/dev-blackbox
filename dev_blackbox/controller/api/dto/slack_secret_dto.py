from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret


class SlackSecretSimpleResponseDto(BaseModel):
    id: int
    name: str

    @classmethod
    def from_entity(cls, entity: SlackSecret) -> SlackSecretSimpleResponseDto:
        return cls(
            id=entity.id,
            name=entity.name,
        )
