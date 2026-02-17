from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.storage.rds.entity.user import User


class GitHubUserSecretInfo(BaseModel):
    id: int
    username: str
    is_active: bool
    deactivate_at: datetime | None

    model_config = {"from_attributes": True}


class JiraUserInfo(BaseModel):
    id: int
    account_id: str
    active: bool
    display_name: str
    email_address: str
    url: str

    model_config = {"from_attributes": True}


class SlackUserInfo(BaseModel):
    id: int
    member_id: str
    display_name: str
    real_name: str
    email: str | None

    model_config = {"from_attributes": True}


class UserWithRelated(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    created_at: datetime
    updated_at: datetime
    github_user_secret: GitHubUserSecretInfo | None = None
    jira_user: JiraUserInfo | None = None
    slack_user: SlackUserInfo | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, user: User) -> "UserWithRelated":
        return cls.model_validate(user)
