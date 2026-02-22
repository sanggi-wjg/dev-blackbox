from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.dto.github_event_dto import (
    GitHubEventResponseDto,
)
from dev_blackbox.core.database import get_db
from dev_blackbox.service.github_event_service import GitHubEventService

router = APIRouter(
    prefix="/github-events",
    tags=["GitHub Event"],
)


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=list[GitHubEventResponseDto],
)
def get_events_by_user_id(user_id: int, db: Session = Depends(get_db)):
    service = GitHubEventService(db)
    events = service.get_events_by_user_id(user_id)
    return events
