from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from dev_blackbox.core.enum import PlatformEnum

if TYPE_CHECKING:
    from dev_blackbox.service.model.event_activity_model import (
        EventContribution,
        EventContributionByDate,
        EventContributionSummary,
    )


class EventContributionSummaryResponseDto(BaseModel):
    total_contributions: int = Field(..., description="전체 기여 수")
    active_days: int = Field(..., description="활동 일수")
    longest_streak: int = Field(..., description="최장 연속 기여 일수")
    current_streak: int = Field(..., description="현재 연속 기여 일수")

    @classmethod
    def from_model(cls, model: EventContributionSummary) -> EventContributionSummaryResponseDto:
        return cls(
            total_contributions=model.total_contributions,
            active_days=model.active_days,
            longest_streak=model.longest_streak,
            current_streak=model.current_streak,
        )


class EventContributionByDateResponseDto(BaseModel):
    event_date: date = Field(..., description="날짜 (YYYY-MM-DD)")
    total_count: int = Field(..., description="해당 날짜 전체 기여 수")
    level: int = Field(..., description="기여 레벨 (0~4)")
    platforms: dict[PlatformEnum, int] = Field(..., description="플랫폼별 기여 수")

    @classmethod
    def from_model(cls, model: EventContributionByDate) -> EventContributionByDateResponseDto:
        return cls(
            event_date=model.event_date,
            total_count=model.count,
            level=model.level,
            platforms=model.platforms,
        )


class EventContributionResponseDto(BaseModel):
    summary: EventContributionSummaryResponseDto
    contributions: list[EventContributionByDateResponseDto]

    @classmethod
    def from_model(cls, model: EventContribution) -> EventContributionResponseDto:
        return cls(
            summary=EventContributionSummaryResponseDto.from_model(model.summary),
            contributions=[
                EventContributionByDateResponseDto.from_model(c) for c in model.contributions
            ],
        )
