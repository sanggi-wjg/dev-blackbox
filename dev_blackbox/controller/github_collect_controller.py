from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from dev_blackbox.core.database import get_db
from dev_blackbox.service.github_collect_service import GitHubCollectService

router = APIRouter(prefix="/collect", tags=["GitHub Collect"])


@router.post(
    "/github",
    status_code=status.HTTP_201_CREATED,
)
async def collect_github_data(
    user_id: int,
    db: Session = Depends(get_db),
):
    github_collect_service = GitHubCollectService(db)
    results = github_collect_service.collect_yesterday_commit_info(user_id)

    return {"message": "Collecting GitHub Data"}
