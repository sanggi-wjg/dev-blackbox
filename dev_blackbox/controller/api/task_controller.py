from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.api.dto.task_dto import (
    TaskCreateRequestDto,
    TaskReorderRequestDto,
    TaskResponseDto,
    TaskUpdateRequestDto,
)
from dev_blackbox.controller.api.param.task_param import TaskParam
from dev_blackbox.controller.config.security_config import CurrentUser, AuthToken
from dev_blackbox.core.database import get_db
from dev_blackbox.service.command.task_command import (
    CreateTaskCommand,
    DeleteTaskCommand,
    ReorderTasksCommand,
    SyncJiraTaskCommand,
    UpdateTaskCommand,
    ArchiveTaskCommand,
    UnarchiveTaskCommand,
)
from dev_blackbox.service.query.task_query import TaskQuery
from dev_blackbox.service.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["Task"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskResponseDto],
)
def get_tasks(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[TaskParam, Query()],
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    query = TaskQuery(
        user_id=current_user.id,
        statuses=param.status,
        is_archived=param.is_archived,
    )
    tasks = service.get_tasks(query)
    return [TaskResponseDto.from_entity(t) for t in tasks]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskResponseDto,
)
def create_task(
    request_dto: TaskCreateRequestDto,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = CreateTaskCommand(
        user_id=current_user.id,
        title=request_dto.title,
        status=request_dto.status,
        content=request_dto.content,
        tags=request_dto.tags,
        display_order=request_dto.display_order,
    )
    task = service.create_task(command)
    return TaskResponseDto.from_entity(task)


@router.post(
    "/{task_id}/jira-sync",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponseDto,
)
def sync_jira_tasks(
    task_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = SyncJiraTaskCommand(
        user_id=current_user.id,
        task_id=task_id,
    )
    task = service.sync_to_jira(command)
    return TaskResponseDto.from_entity(task)


@router.put(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponseDto,
)
def update_task(
    task_id: int,
    request_dto: TaskUpdateRequestDto,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = UpdateTaskCommand(
        task_id=task_id,
        user_id=current_user.id,
        title=request_dto.title,
        content=request_dto.content,
        tags=request_dto.tags,
        status=request_dto.status,
        display_order=request_dto.display_order,
    )
    task = service.update_task(command)
    return TaskResponseDto.from_entity(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = DeleteTaskCommand(task_id=task_id, user_id=current_user.id)
    service.delete_task(command)


@router.patch(
    "/{task_id}/archive",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponseDto,
)
def archive_task(
    task_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = ArchiveTaskCommand(task_id=task_id, user_id=current_user.id)
    task = service.archive_task(command)
    return TaskResponseDto.from_entity(task)


@router.patch(
    "/{task_id}/unarchive",
    status_code=status.HTTP_200_OK,
    response_model=TaskResponseDto,
)
def unarchive_task(
    task_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = UnarchiveTaskCommand(task_id=task_id, user_id=current_user.id)
    task = service.unarchive_task(command)
    return TaskResponseDto.from_entity(task)


@router.patch(
    "/reorder",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskResponseDto],
)
def reorder_tasks(
    request_dto: TaskReorderRequestDto,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    command = ReorderTasksCommand(
        user_id=current_user.id,
        task_ids=request_dto.task_ids,
    )
    tasks = service.reorder_tasks(command)
    return [TaskResponseDto.from_entity(t) for t in tasks]
