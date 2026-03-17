from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status, BackgroundTasks
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.common_dto import BackgroundTaskResponseDto
from dev_blackbox.controller.api.dto.github_event_dto import GitHubEventResponseDto
from dev_blackbox.controller.api.dto.jira_event_dto import JiraEventResponseDto
from dev_blackbox.controller.api.dto.slack_message_dto import SlackMessageResponseDto
from dev_blackbox.controller.api.dto.work_log_dto import (
    PlatformWorkLogDetailResponseDto,
    WorkLogManualSyncReqeustDto,
)
from dev_blackbox.controller.api.param.work_log_param import WorkLogParam
from dev_blackbox.controller.config.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.platform_work_log_service import PlatformWorkLogService
from dev_blackbox.service.query.platform_work_log_query import PlatformWorkLogQuery
from dev_blackbox.task.collect_task import collect_events_and_summarize_work_log_by_user_task
from dev_blackbox.util.idempotent_request import idempotent_request, save_idempotent_response

router = APIRouter(prefix="/api/v1/platform-work-logs", tags=["WorkLog"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[PlatformWorkLogDetailResponseDto],
)
def get_platform_work_logs(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[WorkLogParam, Query()],
    db: Session = Depends(get_db),
):
    service = PlatformWorkLogService(db)
    query = PlatformWorkLogQuery(user_id=current_user.id, target_date=param.target_date)
    sources = service.get_platform_work_logs_with_sources(query)

    result = []
    for wl in sources.work_logs:
        dto = PlatformWorkLogDetailResponseDto.from_entity(wl)
        match wl.platform:
            case PlatformEnum.GITHUB:
                dto.github_events = [
                    GitHubEventResponseDto.from_entity(e) for e in sources.github_events
                ]
            case PlatformEnum.JIRA:
                dto.jira_events = [JiraEventResponseDto.from_entity(e) for e in sources.jira_events]
            case PlatformEnum.SLACK:
                dto.slack_messages = [
                    SlackMessageResponseDto.from_entity(e) for e in sources.slack_messages
                ]
        result.append(dto)
    return result


@router.post(
    "/sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BackgroundTaskResponseDto,
)
async def sync_work_logs(
    request_dto: WorkLogManualSyncReqeustDto,
    request: Request,
    background_tasks: BackgroundTasks,
    token: AuthToken,
    current_user: CurrentUser,
    idempotency_key: str = Depends(idempotent_request),
):
    background_tasks.add_task(
        collect_events_and_summarize_work_log_by_user_task,
        current_user.id,
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
