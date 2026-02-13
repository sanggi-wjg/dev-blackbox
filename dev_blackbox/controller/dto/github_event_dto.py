from datetime import date

from pydantic import BaseModel


class GitHubEventResponseDto(BaseModel):
    id: int
    event_id: str
    target_date: date
    event: dict
    commit: dict | None


class MinimumGitHubEventResponseDto(BaseModel):
    id: int
    event_id: str
    target_date: date
