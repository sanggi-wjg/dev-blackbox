from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

from dev_blackbox.client.model.github_api_model import GithubCommitModel, GithubEventModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.github_event import GitHubEvent


class GitHubEventResponseDto(BaseModel):
    id: int
    event_id: str
    event_type: str
    target_date: date
    event: GithubEventModel
    commit: GithubCommitModel | None

    @classmethod
    def from_entity(cls, entity: GitHubEvent) -> GitHubEventResponseDto:
        return cls(
            id=entity.id,
            event_id=entity.event_id,
            event_type=entity.event_type,
            target_date=entity.target_date,
            event=entity.event_model,
            commit=entity.commit_model,
        )


class MinimumGitHubEventResponseDto(BaseModel):
    id: int
    event_id: str
    event_type: str
    target_date: date

    @classmethod
    def from_entity(cls, entity: GitHubEvent) -> MinimumGitHubEventResponseDto:
        return cls(
            id=entity.id,
            event_id=entity.event_id,
            event_type=entity.event_type,
            target_date=entity.target_date,
        )
