from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.dto.github_collect_dto import CollectGitHubRequestDto
from dev_blackbox.controller.dto.github_event_dto import (
    GitHubEventResponseDto,
    MinimumGitHubEventResponseDto,
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


@router.post(
    "/users/{user_id}/collect",
    status_code=status.HTTP_201_CREATED,
    response_model=list[MinimumGitHubEventResponseDto],
)
def collect_github_events(
    user_id: int,
    request: CollectGitHubRequestDto,
    db: Session = Depends(get_db),
):
    service = GitHubEventService(db)
    events = service.save_github_events(user_id, request.target_date)
    return events
