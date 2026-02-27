from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.slack_message import SlackMessage


class SlackMessageResponseDto(BaseModel):
    id: int
    target_date: date
    channel_id: str
    channel_name: str
    message_ts: str
    message_text: str
    thread_ts: str | None

    @classmethod
    def from_entity(cls, entity: SlackMessage) -> SlackMessageResponseDto:
        return cls(
            id=entity.id,
            target_date=entity.target_date,
            channel_id=entity.channel_id,
            channel_name=entity.channel_name,
            message_ts=entity.message_ts,
            message_text=entity.message_text,
            thread_ts=entity.thread_ts,
        )
