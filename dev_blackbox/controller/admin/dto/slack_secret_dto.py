from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret


class CreateSlackSecretRequestDto(BaseModel):
    name: str
    bot_token: str


class SlackSecretResponseDto(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: SlackSecret) -> SlackSecretResponseDto:
        return cls(
            id=entity.id,
            name=entity.name,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
