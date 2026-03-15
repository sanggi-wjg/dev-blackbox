from datetime import date, datetime

from pydantic import BaseModel, Field

from dev_blackbox.storage.rds.projection.platform_work_log_projection import (
    PlatformWorkLogWithDistanceProjection,
)


class PlatformWorkLogSearchResultDto(BaseModel):
    id: int
    target_date: date = Field(..., description="요약 대상 날짜 (YYYY-MM-DD)")
    platform: str = Field(..., description="플랫폼 이름")
    content: str = Field(..., description="요약 내용")
    score: float = Field(..., description="유사도 점수 (1에 가까울수록 유사)")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_projection(
        cls,
        projection: "PlatformWorkLogWithDistanceProjection",
    ) -> "PlatformWorkLogSearchResultDto":
        entity = projection.platform_work_log
        return cls(
            id=entity.id,
            target_date=entity.target_date,
            platform=entity.platform,
            content=entity.content,
            score=1.0 - projection.distance,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class PlatformWorkLogSearchResponseDto(BaseModel):
    results: list[PlatformWorkLogSearchResultDto]
