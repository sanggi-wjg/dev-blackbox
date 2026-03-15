from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.search_dto import (
    PlatformWorkLogSearchResponseDto,
    PlatformWorkLogSearchResultDto,
)
from dev_blackbox.controller.api.param.search_param import SearchParam
from dev_blackbox.controller.config.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.query.search_query import SearchQuery
from dev_blackbox.service.search_service import SearchService

router = APIRouter(prefix="/api/v1", tags=["Search"])


@router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=PlatformWorkLogSearchResponseDto,
)
async def search_platform_work_logs(
    token: AuthToken,
    current_user: CurrentUser,
    param: Annotated[SearchParam, Query()],
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    query = SearchQuery(
        user_id=current_user.id,
        query_text=param.query,
        limit=param.limit,
    )
    results = service.search_platform_work_logs(query)
    return PlatformWorkLogSearchResponseDto(
        results=[PlatformWorkLogSearchResultDto.from_projection(r) for r in results],
    )
