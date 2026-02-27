from __future__ import annotations

from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.user import User


class UserContext(BaseModel):
    id: int
    tz_info: ZoneInfo
    has_github_user_secret: bool
    has_jira_user: bool
    has_slack_user: bool

    @classmethod
    def from_entity(cls, entity: User) -> UserContext:
        return cls(
            id=entity.id,
            tz_info=entity.tz_info,
            has_github_user_secret=entity.github_user_secret is not None,
            has_jira_user=entity.jira_user is not None,
            has_slack_user=entity.slack_user is not None,
        )
