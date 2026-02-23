from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.controller.api.dto.github_user_secret_dto import GitHubSecretResponseDto
from dev_blackbox.controller.api.dto.jira_user_dto import JiraUserResponseDto
from dev_blackbox.controller.api.dto.slack_user_dto import SlackUserResponseDto


class UserResponseDto(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDetailResponseDto(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    created_at: datetime
    updated_at: datetime
    github_user_secret: GitHubSecretResponseDto | None
    jira_user: JiraUserResponseDto | None
    slack_user: SlackUserResponseDto | None

    model_config = {"from_attributes": True}
