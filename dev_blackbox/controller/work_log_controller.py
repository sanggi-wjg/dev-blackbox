from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.dto.work_log_dto import (
    DailyWorkLogResponseDto,
    PlatformWorkLogResponseDto,
    WorkLogQuery,
)
from dev_blackbox.core.database import get_db
from dev_blackbox.service.work_log_service import WorkLogService

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
    "/users/{user_id}/daily",
    status_code=status.HTTP_200_OK,
    response_model=DailyWorkLogResponseDto | None,
)
async def get_daily_work_logs(
    user_id: int,
    query: Annotated[WorkLogQuery, Query()],
    db: Session = Depends(get_db),
):
    service = WorkLogService(db)
    return service.get_daily_work_log(
        user_id=user_id,
        target_date=query.target_date,
    )
