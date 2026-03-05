from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from dev_blackbox.core.enum import TaskStatusEnum

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.task import Task


class TaskResponseDto(BaseModel):
    id: int
    title: str
    content: str
    tags: str | None
    status: TaskStatusEnum
    is_archived: bool
    display_order: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Task) -> TaskResponseDto:
        return cls(
            id=entity.id,
            title=entity.title,
            content=entity.content,
            tags=entity.tags,
            status=entity.status,
            is_archived=entity.is_archived,
            display_order=entity.display_order,
            archived_at=entity.archived_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TaskCreateRequestDto(BaseModel):
    title: str = Field(..., description="태스크 제목")
    status: TaskStatusEnum = Field(..., description="태스크 상태")
    content: str = Field(default="", description="태스크 내용")
    tags: str | None = Field(default=None, description="태스크 태그")
    display_order: int = Field(default=0, description="표시 순서")


class TaskReorderRequestDto(BaseModel):
    task_ids: list[int] = Field(..., description="정렬된 태스크 ID 리스트")


class TaskUpdateRequestDto(BaseModel):
    title: str = Field(..., description="태스크 제목")
    content: str = Field(default="", description="태스크 내용")
    tags: str | None = Field(default=None, description="태스크 태그")
    status: TaskStatusEnum = Field(..., description="태스크 상태")
    display_order: int = Field(default=0, description="표시 순서")
