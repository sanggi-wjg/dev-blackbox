from datetime import date

from pydantic import BaseModel

from dev_blackbox.client.model.github_api_model import GithubCommitModel, GithubEventModel


class GitHubEventResponseDto(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    event_id: str
    event_type: str
    target_date: date
    event: GithubEventModel
    commit: GithubCommitModel | None


class MinimumGitHubEventResponseDto(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    event_id: str
    event_type: str
    target_date: date
