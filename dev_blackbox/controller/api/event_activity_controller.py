from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.event_activity_dto import EventContributionResponseDto
from dev_blackbox.controller.api.param.event_activity_param import EventActivityHeatmapParam
from dev_blackbox.controller.config.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.event_activity_service import EventActivityService
from dev_blackbox.service.query.event_activity_query import EventContributionQuery

router = APIRouter(prefix="/api/v1/event-activity", tags=["Event Activity"])


@router.get(
    "/heatmap",
    status_code=status.HTTP_200_OK,
    response_model=EventContributionResponseDto,
)
async def get_event_activity_heatmap(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[EventActivityHeatmapParam, Query()],
    db: Session = Depends(get_db),
):
    service = EventActivityService(db)
    query = EventContributionQuery(
        from_date=param.from_date,
        to_date=param.to_date,
        user_id=current_user.id,
    )
    result = service.get_event_contribution(query)
    return EventContributionResponseDto.from_model(result)
