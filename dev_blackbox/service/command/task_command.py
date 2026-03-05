from pydantic import BaseModel

from dev_blackbox.core.enum import TaskStatusEnum


class CreateTaskCommand(BaseModel):
    user_id: int
    title: str
    status: TaskStatusEnum
    content: str
    tags: str | None
    display_order: int


class ReorderTasksCommand(BaseModel):
    user_id: int
    task_ids: list[int]


class UpdateTaskCommand(BaseModel):
    task_id: int
    user_id: int
    title: str
    content: str
    tags: str | None
    status: TaskStatusEnum
    display_order: int


class DeleteTaskCommand(BaseModel):
    task_id: int
    user_id: int
