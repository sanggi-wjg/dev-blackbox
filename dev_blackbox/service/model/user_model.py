from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class GitHubUserSecretModel(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class JiraUserModel(BaseModel):
    id: int
    account_id: str
    active: bool
    display_name: str
    email_address: str
    url: str

    model_config = {"from_attributes": True}


class SlackUserModel(BaseModel):
    id: int
    member_id: str
    display_name: str
    real_name: str
    email: str | None

    model_config = {"from_attributes": True}


class UserModel(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserWithPlatformInfoModel(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    created_at: datetime
    updated_at: datetime
    github_user_secret: GitHubUserSecretModel | None = None
    jira_user: JiraUserModel | None = None
    slack_user: SlackUserModel | None = None

    model_config = {"from_attributes": True}
