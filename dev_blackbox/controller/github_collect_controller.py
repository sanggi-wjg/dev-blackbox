from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.controller.dto.github_collect_dto import CollectGitHubRequestDto
from dev_blackbox.core.database import get_db
from dev_blackbox.service.github_collect_service import GitHubCollectService

router = APIRouter(prefix="/collect", tags=["GitHub Collect"])


@router.post(
    "/github/users/{user_id}",
    status_code=status.HTTP_201_CREATED,
)
async def collect_github_data(
    request: CollectGitHubRequestDto,
    db: Session = Depends(get_db),
):
    github_collect_service = GitHubCollectService(db)
    github_collect_service.collect_github_events(request.user_id, request.target_date)
    return {"message": "Collecting GitHub Data"}
