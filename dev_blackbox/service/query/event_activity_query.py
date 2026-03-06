from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from dev_blackbox.core.enum import PlatformEnum


class EventContributionGroupBy(StrEnum):
    DATE = "date"


class EventContributionQuery(BaseModel):
    from_date: date
    to_date: date
    user_id: int
    platforms: list[PlatformEnum] | None = None
    group_by: EventContributionGroupBy = EventContributionGroupBy.DATE
