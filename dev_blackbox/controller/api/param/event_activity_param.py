from datetime import date

from pydantic import BaseModel, Field


class EventActivityHeatmapParam(BaseModel):
    from_date: date = Field(..., description="조회 시작 날짜 (YYYY-MM-DD)")
    to_date: date = Field(..., description="조회 종료 날짜 (YYYY-MM-DD)")
