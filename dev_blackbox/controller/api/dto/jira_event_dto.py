from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

from dev_blackbox.client.model.jira_api_model import (
    JiraChangelogHistoryModel,
    JiraIssueModel,
)

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.jira_event import JiraEvent


class JiraEventResponseDto(BaseModel):
    id: int
    issue_id: str
    issue_key: str
    target_date: date
    issue: JiraIssueModel
    changelog: list[JiraChangelogHistoryModel] | None

    @classmethod
    def from_entity(cls, entity: JiraEvent) -> JiraEventResponseDto:
        return cls(
            id=entity.id,
            issue_id=entity.issue_id,
            issue_key=entity.issue_key,
            target_date=entity.target_date,
            issue=entity.issue_model,
            changelog=(
                [JiraChangelogHistoryModel.model_validate(c) for c in entity.changelog]
                if entity.changelog
                else None
            ),
        )
