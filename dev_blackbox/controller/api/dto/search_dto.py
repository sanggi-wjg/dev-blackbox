from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from dev_blackbox.service.model.search_model import (
        PlatformWorkLogSearchResult,
        ChunkSearchResult,
    )


class PlatformWorkLogChunkSearchResultDto(BaseModel):
    chunk_index: int
    chunk_text: str
    score: float

    @classmethod
    def from_model(cls, model: "ChunkSearchResult") -> "PlatformWorkLogChunkSearchResultDto":
        return cls(
            chunk_index=model.chunk_index,
            chunk_text=model.chunk_text,
            score=1 - model.distance,
        )


class PlatformWorkLogSearchResultDto(BaseModel):
    id: int
    target_date: date = Field(..., description="요약 대상 날짜 (YYYY-MM-DD)")
    platform: str = Field(..., description="플랫폼 이름")
    content: str = Field(..., description="요약 내용")
    score: float = Field(..., description="유사도 점수 (1에 가까울수록 유사)")
    created_at: datetime
    updated_at: datetime
    chunk_result: list[PlatformWorkLogChunkSearchResultDto] = Field(
        ..., description="유사한 청크 검색 결과 목록"
    )
    chunk_count: int = Field(..., description="유사한 청크 검색 결과 수")

    @classmethod
    def from_model(cls, model: "PlatformWorkLogSearchResult") -> "PlatformWorkLogSearchResultDto":
        entity = model.platform_work_log
        return cls(
            id=entity.id,
            target_date=entity.target_date,
            platform=entity.platform,
            content=entity.content,
            score=1.0 - model.distance,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            chunk_result=[
                PlatformWorkLogChunkSearchResultDto.from_model(r) for r in model.chunk_results
            ],
            chunk_count=model.chunk_count,
        )


class PlatformWorkLogSearchResponseDto(BaseModel):
    results: list[PlatformWorkLogSearchResultDto]
