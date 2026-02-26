from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.core.encrypt import EncryptService
    from dev_blackbox.storage.rds.entity import JiraUser


class JiraUserModel(BaseModel):
    model_config = {"from_attributes": True}

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
    def from_entity(
        cls,
        entity: JiraUser,
        encrypt_service: EncryptService,
    ) -> JiraUserModel:
        return cls(
            id=entity.id,
            jira_secret_id=entity.jira_secret_id,
            account_id=entity.account_id,
            is_active=entity.is_active,
            display_name=encrypt_service.decrypt(entity.display_name),
            email_address=encrypt_service.decrypt(entity.email_address),
            url=entity.url,
            project=entity.project,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
