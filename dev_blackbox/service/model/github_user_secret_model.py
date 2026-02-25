from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity import GitHubUserSecret
    from dev_blackbox.core.encrypt import EncryptService


class GitHubUserSecretModel(BaseModel):
    id: int
    username: str
    personal_access_token: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(
        cls,
        entity: GitHubUserSecret,
        encrypt_service: EncryptService,
    ) -> GitHubUserSecretModel:
        return cls(
            id=entity.id,
            username=entity.username,
            personal_access_token=encrypt_service.decrypt(entity.personal_access_token),
        )
