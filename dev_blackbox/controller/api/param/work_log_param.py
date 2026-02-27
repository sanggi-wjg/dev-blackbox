from datetime import date

from pydantic import BaseModel, Field


class WorkLogParam(BaseModel):
    target_date: date = Field(..., description="조회 대상 날짜 (YYYY-MM-DD)")
