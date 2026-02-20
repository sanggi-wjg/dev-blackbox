from datetime import date, datetime

from pydantic import BaseModel, Field


class WorkLogQuery(BaseModel):
    target_date: date = Field(..., description="조회 대상 날짜 (YYYY-MM-DD)")


class PlatformWorkLogResponseDto(BaseModel):
    id: int
    target_date: date
    platform: str
    summary: str
    model_name: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyWorkLogResponseDto(BaseModel):
    id: int
    target_date: date
    summary: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
