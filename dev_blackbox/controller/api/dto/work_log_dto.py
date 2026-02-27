from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from dev_blackbox.controller.api.dto.github_event_dto import GitHubEventResponseDto
from dev_blackbox.controller.api.dto.jira_event_dto import JiraEventResponseDto
from dev_blackbox.controller.api.dto.slack_message_dto import SlackMessageResponseDto

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
    from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog


class WorkLogQuery(BaseModel):
    target_date: date = Field(..., description="조회 대상 날짜 (YYYY-MM-DD)")


class PlatformWorkLogResponseDto(BaseModel):
    id: int
    target_date: date = Field(..., description="요약 대상 날짜 (YYYY-MM-DD)")
    platform: str = Field(..., description="플랫폼 이름")
    content: str = Field(..., description="요약 내용")
    model_name: str = Field(..., description="사용된 모델 이름")
    prompt: str = Field(..., description="사용된 프롬프트 템플릿")
    user_id: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: PlatformWorkLog) -> PlatformWorkLogResponseDto:
        return cls(
            id=entity.id,
            target_date=entity.target_date,
            platform=entity.platform,
            content=entity.content,
            model_name=entity.model_name,
            prompt=entity.prompt,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class DailyWorkLogResponseDto(BaseModel):
    id: int
    target_date: date = Field(..., description="요약 대상 날짜 (YYYY-MM-DD)")
    content: str = Field(..., description="요약 내용")
    user_id: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: DailyWorkLog) -> DailyWorkLogResponseDto:
        return cls(
            id=entity.id,
            target_date=entity.target_date,
            content=entity.content,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class WorkLogManualSyncReqeustDto(BaseModel):
    target_date: date = Field(..., description="수동 수집 대상 날짜 (YYYY-MM-DD)")


class PlatformWorkLogDetailResponseDto(BaseModel):
    id: int
    target_date: date = Field(..., description="요약 대상 날짜 (YYYY-MM-DD)")
    platform: str = Field(..., description="플랫폼 이름")
    content: str = Field(..., description="요약 내용")
    model_name: str = Field(..., description="사용된 모델 이름")
    prompt: str = Field(..., description="사용된 프롬프트 템플릿")
    user_id: int
    created_at: datetime
    updated_at: datetime
    github_events: list[GitHubEventResponseDto] = []
    jira_events: list[JiraEventResponseDto] = []
    slack_messages: list[SlackMessageResponseDto] = []

    @classmethod
    def from_entity(cls, entity: PlatformWorkLog) -> PlatformWorkLogDetailResponseDto:
        return cls(
            id=entity.id,
            target_date=entity.target_date,
            platform=entity.platform,
            content=entity.content,
            model_name=entity.model_name,
            prompt=entity.prompt,
            user_id=entity.user_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class UserContentCreateOrUpdateRequestDto(BaseModel):
    target_date: date = Field(..., description="사용자 콘텐츠의 대상 날짜 (YYYY-MM-DD)")
    content: str = Field(..., description="사용자 콘텐츠")
