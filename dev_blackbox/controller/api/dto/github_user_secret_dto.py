from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

from dev_blackbox.core.types import NotBlankStr
from dev_blackbox.util.mask_util import mask

if TYPE_CHECKING:
    from dev_blackbox.core.encrypt import EncryptService
    from dev_blackbox.storage.rds.entity import GitHubUserSecret


class CreateGitHubSecretRequestDto(BaseModel):
    username: NotBlankStr
    personal_access_token: NotBlankStr


class GitHubSecretResponseDto(BaseModel):
    id: int
    username: str
    personal_access_token: str

    @field_validator("personal_access_token")
    @classmethod
    def mask_token(cls, v: str) -> str:
        return mask(v, 10)

    @classmethod
    def from_entity(
        cls, entity: GitHubUserSecret, encrypt_service: EncryptService
    ) -> GitHubSecretResponseDto:
        return cls(
            id=entity.id,
            username=entity.username,
            personal_access_token=encrypt_service.decrypt(entity.personal_access_token),
        )
