from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status, BackgroundTasks, Response
from sqlalchemy.orm import Session

from dev_blackbox.controller.dto.common_dto import BackgroundTaskResponseDto
from dev_blackbox.controller.dto.work_log_dto import (
    DailyWorkLogResponseDto,
    PlatformWorkLogResponseDto,
    WorkLogQuery,
    WorkLogManualSyncReqeustDto,
    UserContentCreateOrUpdateRequestDto,
)
from dev_blackbox.core.database import get_db
from dev_blackbox.service.work_log_service import WorkLogService
from dev_blackbox.task.collect_task import collect_events_and_summarize_work_log_by_user_task
from dev_blackbox.util.idempotent_request import idempotent_request, save_idempotent_response

router = APIRouter(prefix="/work-logs", tags=["WorkLog"])


@router.get(
    "/users/{user_id}/platforms",
    status_code=status.HTTP_200_OK,
    response_model=list[PlatformWorkLogResponseDto],
)
async def get_platform_work_logs(
    user_id: int,
    query: Annotated[WorkLogQuery, Query()],
    db: Session = Depends(get_db),
):
    service = WorkLogService(db)
    return service.get_platform_work_logs(
        user_id=user_id,
        target_date=query.target_date,
    )


@router.get(
    "/users/{user_id}/user-content",
    status_code=status.HTTP_200_OK,
    response_model=PlatformWorkLogResponseDto | None,
)
async def get_user_content(
    user_id: int,
    query: Annotated[WorkLogQuery, Query()],
    response: Response,
    db: Session = Depends(get_db),
):
    service = WorkLogService(db)
    work_log = service.get_user_content_or_none(
        user_id=user_id,
        target_date=query.target_date,
    )
    if work_log is None:
        response.status_code = status.HTTP_204_NO_CONTENT
    return work_log


@router.put(
    "/users/{user_id}/user-content",
    status_code=status.HTTP_200_OK,
    response_model=PlatformWorkLogResponseDto,
)
async def create_or_update_user_content(
    user_id: int,
    request_dto: UserContentCreateOrUpdateRequestDto,
    response: Response,
    db: Session = Depends(get_db),
):
    service = WorkLogService(db)
    is_created, work_log = service.create_or_update_user_content(
        user_id=user_id,
        target_date=request_dto.target_date,
        content=request_dto.content,
    )
    if is_created:
        response.status_code = status.HTTP_201_CREATED
    return work_log


@router.get(
    "/users/{user_id}/daily",
    status_code=status.HTTP_200_OK,
    response_model=DailyWorkLogResponseDto | None,
)
async def get_daily_work_log(
    user_id: int,
    query: Annotated[WorkLogQuery, Query()],
    db: Session = Depends(get_db),
):
    service = WorkLogService(db)
    return service.get_daily_work_log(
        user_id=user_id,
        target_date=query.target_date,
    )


@router.post(
    "/{user_id}/manual-sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BackgroundTaskResponseDto,
)
async def sync_work_logs(
    user_id: int,
    request_dto: WorkLogManualSyncReqeustDto,
    request: Request,
    background_tasks: BackgroundTasks,
    idempotency_key: str = Depends(idempotent_request),
):
    background_tasks.add_task(
        collect_events_and_summarize_work_log_by_user_task,
        user_id,
        request_dto.target_date,
    )
    response = BackgroundTaskResponseDto(
        message=f"{request_dto.target_date}에 대해 수동 동기화 작업이 시작 되었습니다."
    )
    save_idempotent_response(
        request=request,
        idempotency_key=idempotency_key,
        response_data=response.model_dump(mode="json"),
    )
    return response
