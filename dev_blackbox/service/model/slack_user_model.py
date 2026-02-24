from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.core.encrypt import EncryptService
    from dev_blackbox.storage.rds.entity.slack_user import SlackUser


class SlackUserModel(BaseModel):
    id: int
    member_id: str
    display_name: str
    real_name: str
    email: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(
        cls,
        entity: SlackUser,
        encrypt_service: EncryptService,
    ) -> SlackUserModel:
        return cls(
            id=entity.id,
            member_id=entity.member_id,
            display_name=encrypt_service.decrypt(entity.display_name),
            real_name=encrypt_service.decrypt(entity.real_name),
            email=encrypt_service.decrypt(entity.email) if entity.email else None,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
