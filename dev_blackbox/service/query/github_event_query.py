from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from dev_blackbox.service.query.common_query import OrderDirection


class GitHubEventOrderField(StrEnum):
    ID = "id"


class GitHubEventsByUserQuery(BaseModel):
    user_id: int
    order_by: list[tuple[GitHubEventOrderField, OrderDirection]] = [
        (GitHubEventOrderField.ID, OrderDirection.ASC)
    ]


class GitHubEventsByEventTypesQuery(BaseModel):
    user_id: int
    target_date: date
    event_types: list[str]
    order_by: list[tuple[GitHubEventOrderField, OrderDirection]] = [
        (GitHubEventOrderField.ID, OrderDirection.ASC)
    ]
