from datetime import date

from pydantic import BaseModel, Field

from dev_blackbox.core.enum import PlatformEnum


class SearchParam(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
    similarity: float = Field(0.5, ge=0.0, le=1.0)
    platform: PlatformEnum | None = Field(None, description="플랫폼 필터 (GITHUB, JIRA, SLACK 등)")
    from_date: date | None = Field(None, description="검색 시작 날짜 (YYYY-MM-DD)")
    to_date: date | None = Field(None, description="검색 종료 날짜 (YYYY-MM-DD)")
