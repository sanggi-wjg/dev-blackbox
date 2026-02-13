from datetime import datetime

from pydantic import BaseModel

from dev_blackbox.core.types import NotBlankStr


class CreateGitHubSecretRequestDto(BaseModel):
    username: NotBlankStr
    personal_access_token: NotBlankStr
    user_id: int


class GitHubSecretResponseDto(BaseModel):
    id: int
    username: str
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
