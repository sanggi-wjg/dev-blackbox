from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.work_log_dto import DailyWorkLogResponseDto
from dev_blackbox.controller.api.param.work_log_param import WorkLogParam
from dev_blackbox.controller.config.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.daily_work_log_service import DailyWorkLogService
from dev_blackbox.service.query.daily_work_log_query import DailyWorkLogQuery

router = APIRouter(prefix="/api/v1/daily-work-logs", tags=["WorkLog"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=DailyWorkLogResponseDto | None,
)
async def get_daily_work_log(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[WorkLogParam, Query()],
    db: Session = Depends(get_db),
):
    service = DailyWorkLogService(db)
    query = DailyWorkLogQuery(user_id=current_user.id, target_date=param.target_date)
    daily_work_log = service.get_daily_work_log(query)
    if daily_work_log is None:
        return None
    return DailyWorkLogResponseDto.from_entity(daily_work_log)
