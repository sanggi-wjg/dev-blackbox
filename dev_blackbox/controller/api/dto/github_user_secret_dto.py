from pydantic import BaseModel

from dev_blackbox.core.types import NotBlankStr


class CreateGitHubSecretRequestDto(BaseModel):
    username: NotBlankStr
    personal_access_token: NotBlankStr


class GitHubSecretResponseDto(BaseModel):
    id: int
    username: str
    personal_access_token: str

    model_config = {"from_attributes": True}
