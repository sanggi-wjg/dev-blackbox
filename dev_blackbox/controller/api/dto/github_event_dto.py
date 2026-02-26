from datetime import date

from pydantic import BaseModel

from dev_blackbox.client.model.github_api_model import GithubCommitModel, GithubEventModel


class GitHubEventResponseDto(BaseModel):
    id: int
    event_id: str
    event_type: str
    target_date: date
    event: GithubEventModel
    commit: GithubCommitModel | None

    model_config = {"from_attributes": True}


class MinimumGitHubEventResponseDto(BaseModel):
    id: int
    event_id: str
    event_type: str
    target_date: date

    model_config = {"from_attributes": True}
