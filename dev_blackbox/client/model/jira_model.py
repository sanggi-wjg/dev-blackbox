from datetime import date
from functools import cached_property
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.util.datetime_util import get_date_from_iso_format

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
    IN_FLIGHT_AND_RESOLVED: list[JiraIssueStatus] = [
        "In Progress",
        "In Dev Review",
        "Ready For QA",
        "In QA",
        "Ready For Release",
        "Done",
        "Closed",
    ]


class JQL(BaseModel):
    pass


class IssueJQL(JQL):
    project: str | None = None
    assignee_account_id: str | None = None
    include_status: JiraIssueStatus | None = None
    include_statuses: list[JiraIssueStatus] | None = None
    updated_within: str | None = None
    updated_after: str | None = None  # 절대 날짜 (e.g. "2024-01-15")
    updated_before: str | None = None  # 절대 날짜 (e.g. "2024-01-16")
    order_by: str | None = "updatedDate DESC"

    def build(self) -> str:
        conditions: list[str] = []

        if self.project:
            conditions.append(f"project = '{self.project}'")

        if self.assignee_account_id:
            conditions.append(f"assignee = '{self.assignee_account_id}'")

        if self.include_status:
            conditions.append(f"status = '{self.include_status}'")

        if self.include_statuses:
            quoted = [f"'{s}'" for s in self.include_statuses]
            conditions.append(f"status in ({', '.join(quoted)})")

        if self.updated_within:
            conditions.append(f"updatedDate >= {self.updated_within}")

        if self.updated_after:
            conditions.append(f"updatedDate >= '{self.updated_after}'")

        if self.updated_before:
            conditions.append(f"updatedDate < '{self.updated_before}'")

        jql = " AND ".join(conditions)

        if self.order_by:
            jql += f" ORDER BY {self.order_by}"

        return jql


class JiraChangelogItemModel(BaseModel):
    """changelog.histories[].items[] 항목"""

    field: str
    from_string: str | None = None
    to_string: str | None = None


class JiraChangelogHistoryModel(BaseModel):
    """changelog.histories[] 항목"""

    id: str
    created: str  # ISO 8601 형식
    items: list[JiraChangelogItemModel]

    def get_created_date(self, tz_info: ZoneInfo) -> date:
        return get_date_from_iso_format(self.created, tz_info=tz_info)


class JiraCommentModel(BaseModel):
    """issue.fields.comment.comments[] 항목"""

    author_display_name: str
    body: str
    created: str  # ISO 8601 형식

    def get_created_date(self, tz_info: ZoneInfo) -> date:
        return get_date_from_iso_format(self.created, tz_info=tz_info)


class JiraIssueModel(BaseModel):
    """Jira Issue를 구조화한 모델. issue.raw dict에서 파싱."""

    key: str  # "FMP-123"
    summary: str
    status: str
    issue_type: str  # Bug, Story, Task
    priority: str | None = None
    labels: list[str] = []
    assignee_display_name: str | None = None
    comments: list[JiraCommentModel] = []
    changelog_histories: list[JiraChangelogHistoryModel] = []

    @classmethod
    def from_raw(cls, raw: dict) -> "JiraIssueModel":
        """issue.raw dict에서 JiraIssueModel 생성"""
        fields = raw.get("fields", {})

        # 코멘트 파싱
        comment_data = fields.get("comment", {})
        comments_raw = comment_data.get("comments", []) if isinstance(comment_data, dict) else []
        comments = [
            JiraCommentModel(
                author_display_name=c.get("author", {}).get("displayName", ""),
                body=c.get("body", ""),
                created=c.get("created", ""),
            )
            for c in comments_raw
        ]

        # changelog 파싱
        changelog_data = raw.get("changelog", {})
        histories_raw = changelog_data.get("histories", [])
        histories = [
            JiraChangelogHistoryModel(
                id=h.get("id", ""),
                created=h.get("created", ""),
                items=[
                    JiraChangelogItemModel(
                        field=item.get("field", ""),
                        from_string=item.get("fromString"),
                        to_string=item.get("toString"),
                    )
                    for item in h.get("items", [])
                ],
            )
            for h in histories_raw
        ]

        return cls(
            key=raw.get("key", ""),
            summary=fields.get("summary", ""),
            status=(fields.get("status") or {}).get("name", ""),
            issue_type=(fields.get("issuetype") or {}).get("name", ""),
            priority=(fields.get("priority") or {}).get("name"),
            labels=fields.get("labels", []),
            assignee_display_name=(fields.get("assignee") or {}).get("displayName"),
            comments=comments,
            changelog_histories=histories,
        )

    def filter_changelog_by_date(
        self, target_date: date, tz_info: ZoneInfo
    ) -> list[JiraChangelogHistoryModel]:
        """target_date에 해당하는 changelog만 필터링"""
        return [h for h in self.changelog_histories if h.get_created_date(tz_info) == target_date]

    def filter_comments_by_date(
        self, target_date: date, tz_info: ZoneInfo
    ) -> list[JiraCommentModel]:
        """target_date에 해당하는 코멘트만 필터링"""
        return [c for c in self.comments if c.get_created_date(tz_info) == target_date]

    @cached_property
    def _base_info_text(self) -> str:
        """이슈 기본 정보 텍스트"""
        lines = [
            f"[{self.key}] {self.issue_type}: {self.summary}",
            f"현재 상태: {self.status}",
        ]
        if self.priority:
            lines.append(f"우선순위: {self.priority}")
        if self.labels:
            lines.append(f'라벨: {", ".join(self.labels)}')
        return "\n".join(lines)

    def issue_detail_text(self, target_date: date, tz_info: ZoneInfo) -> str:
        """LLM에 전달할 이슈 상세 텍스트 생성 (target_date 기준 필터링)"""
        lines = [self._base_info_text]

        # target_date changelog만
        filtered_changelog = self.filter_changelog_by_date(target_date, tz_info)
        if filtered_changelog:
            lines.append("변경 이력:")
            for history in filtered_changelog:
                for item in history.items:
                    if item.field == "status":
                        time_str = history.created[:19]
                        lines.append(f"- 상태: {item.from_string} → {item.to_string} ({time_str})")

        # target_date 코멘트만
        filtered_comments = self.filter_comments_by_date(target_date, tz_info)
        if filtered_comments:
            lines.append("코멘트:")
            for comment in filtered_comments:
                time_str = comment.created[:19]
                # 코멘트 본문이 너무 길면 잘라내기 (LLM context 절약)
                body = comment.body[:500] if len(comment.body) > 500 else comment.body
                lines.append(f"- ({time_str}) {body}")

        return "\n".join(lines)
