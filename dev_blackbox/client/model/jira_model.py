from typing import Literal

from pydantic import BaseModel

JiraIssueStatus = Literal[
    "Backlog",
    "Open",
    "In Progress",
    "In Dev Review",
    "Ready For QA",
    "In QA",
    "Ready For Release",
    "Done",
    "Closed",
    # etc
    "Cancelled",
    "Hold",
]


class JiraStatusGroup:
    ALL: list[JiraIssueStatus] = [
        "Backlog",
        "Open",
        "In Progress",
        "In Dev Review",
        "Ready For QA",
        "In QA",
        "Ready For Release",
        "Done",
        "Closed",
        "Cancelled",
        "Hold",
    ]
    IN_FLIGHT: list[JiraIssueStatus] = [
        "In Progress",
        "In Dev Review",
        "Ready For QA",
        "In QA",
        "Ready For Release",
    ]
    RESOLVED: list[JiraIssueStatus] = [
        "Done",
        "Closed",
    ]
    TRACKED: list[JiraIssueStatus] = [
        "In Progress",
        "In Dev Review",
        "Ready For QA",
        "In QA",
        "Ready For Release",
        "Done",
        "Closed",
    ]


class JQL(BaseModel):

    def build(self) -> str:
        raise NotImplementedError


class IssueJQL(JQL):
    project: str | None = None
    assignee_account_id: str | None = None
    include_status: JiraIssueStatus | None = None
    include_statuses: list[JiraIssueStatus] | None
    updated_within: str | None = "-30d"
    order_by: str | None = "updatedDate DESC"

    def build(self) -> str:
        conditions: list[str] = []

        if self.project:
            conditions.append(f"project = {self.project}")

        if self.assignee_account_id:
            conditions.append(f"assignee = {self.assignee_account_id}")

        if self.include_status:
            conditions.append(f"status = {self.include_status}")

        if self.include_statuses:
            quoted = [f"'{s}'" for s in self.include_statuses]
            conditions.append(f"status in ({', '.join(quoted)})")

        if self.updated_within:
            conditions.append(f"updatedDate >= {self.updated_within}")

        jql = " AND ".join(conditions)

        if self.order_by:
            jql += f" ORDER BY {self.order_by}"

        return jql
