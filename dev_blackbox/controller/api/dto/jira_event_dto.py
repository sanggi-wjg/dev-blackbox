from datetime import date

from pydantic import BaseModel

from dev_blackbox.client.model.jira_api_model import (
    JiraChangelogHistoryModel,
    JiraIssueModel,
)


class JiraEventResponseDto(BaseModel):
    id: int
    issue_id: str
    issue_key: str
    target_date: date
    issue: JiraIssueModel
    changelog: list[JiraChangelogHistoryModel] | None

    model_config = {"from_attributes": True}
