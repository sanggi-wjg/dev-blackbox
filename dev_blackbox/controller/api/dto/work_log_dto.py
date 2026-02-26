from datetime import date, datetime

from pydantic import BaseModel, Field

from dev_blackbox.controller.api.dto.github_event_dto import GitHubEventResponseDto
from dev_blackbox.controller.api.dto.jira_event_dto import JiraEventResponseDto
from dev_blackbox.controller.api.dto.slack_message_dto import SlackMessageResponseDto


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

    model_config = {"from_attributes": True}


class DailyWorkLogResponseDto(BaseModel):
    id: int
    target_date: date = Field(..., description="요약 대상 날짜 (YYYY-MM-DD)")
    content: str = Field(..., description="요약 내용")
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


class UserContentCreateOrUpdateRequestDto(BaseModel):
    target_date: date = Field(..., description="사용자 콘텐츠의 대상 날짜 (YYYY-MM-DD)")
    content: str = Field(..., description="사용자 콘텐츠")
