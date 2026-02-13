from datetime import date

from pydantic import BaseModel


class CollectGitHubRequestDto(BaseModel):
    user_id: int
    target_date: date | None = None  # null일 경우 어제 날짜로 설정
