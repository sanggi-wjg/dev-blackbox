from pydantic import BaseModel, field_validator

from dev_blackbox.core.types import NotBlankStr
from dev_blackbox.util.mask_util import mask


class CreateGitHubSecretRequestDto(BaseModel):
    username: NotBlankStr
    personal_access_token: NotBlankStr


class GitHubSecretResponseDto(BaseModel):
    id: int
    username: str
    personal_access_token: str

    model_config = {"from_attributes": True}

    @field_validator("personal_access_token")
    @classmethod
    def mask_token(cls, v: str) -> str:
        return mask(v, 10)
