from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.service.model.slack_user_model import SlackUserModel


class SlackUserResponseDto(BaseModel):
    id: int
    slack_secret_id: int
    member_id: str
    is_active: bool
    display_name: str
    real_name: str
    email: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: SlackUserModel) -> SlackUserResponseDto:
        return cls(
            id=model.id,
            slack_secret_id=model.slack_secret_id,
            member_id=model.member_id,
            is_active=model.is_active,
            display_name=model.display_name,
            real_name=model.real_name,
            email=model.email,
            user_id=model.user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class AssignSlackUserRequestDto(BaseModel):
    slack_secret_id: int
    slack_user_id: int
