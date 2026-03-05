from pydantic import BaseModel, Field

from dev_blackbox.core.enum import TaskStatusEnum


class TaskParam(BaseModel):
    status: list[TaskStatusEnum] | None = Field(default=None, description="태스크 상태 필터")
    is_archived: bool = Field(default=False, description="아카이브 여부")
