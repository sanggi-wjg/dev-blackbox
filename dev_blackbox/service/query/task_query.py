from pydantic import BaseModel

from dev_blackbox.core.enum import TaskStatusEnum


class TaskQuery(BaseModel):
    user_id: int
    statuses: list[TaskStatusEnum] | None = None
    is_archived: bool = False
