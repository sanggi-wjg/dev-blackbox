from datetime import date

from pydantic import BaseModel

from dev_blackbox.core.enum import PlatformEnum


class EventContributionSummary(BaseModel):
    total_contributions: int
    active_days: int
    longest_streak: int
    current_streak: int


class EventContributionByDate(BaseModel):
    event_date: date
    count: int
    level: int
    platforms: dict[PlatformEnum, int]


class EventContribution(BaseModel):
    summary: EventContributionSummary
    contributions: list[EventContributionByDate]
