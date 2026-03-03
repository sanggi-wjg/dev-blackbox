from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.client.model.jira_api_model import IssueJQL


def _create_jira_user(
    account_id: str = "acc-001",
    display_name: str = "Alice",
):
    return SimpleNamespace(
        accountId=account_id,
        displayName=display_name,
    )


def _create_jira_issue(
    key: str = "DEV-1",
    summary: str = "버그 수정",
):
    return SimpleNamespace(
        key=key,
        fields=SimpleNamespace(summary=summary),
    )


class JiraClientTest:

    def setup_method(self):
        self.mock_jira = MagicMock()
        with patch("dev_blackbox.client.jira_client.JIRA", return_value=self.mock_jira):
            self.jira_client = JiraClient("https://jira.example.com", "user", "token")

    # -- fetch_assignable_users --

    def test_fetch_assignable_users_프로젝트의_할당_가능_사용자를_반환한다(self):
        # given
        self.mock_jira.search_assignable_users_for_projects.return_value = [
            _create_jira_user("acc-001", "Alice"),
            _create_jira_user("acc-002", "Bob"),
        ]

        # when
        result = self.jira_client.fetch_assignable_users("DEV")

        # then
        assert len(result) == 2
        self.mock_jira.search_assignable_users_for_projects.assert_called_once_with(
            "", projectKeys="DEV"
        )

    def test_fetch_assignable_users_사용자가_없으면_빈_리스트를_반환한다(self):
        # given
        self.mock_jira.search_assignable_users_for_projects.return_value = []

        # when
        result = self.jira_client.fetch_assignable_users("DEV")

        # then
        assert len(result) == 0

    # -- fetch_search_issues --

    def test_fetch_search_issues_JQL로_이슈를_조회한다(self):
        # given
        jql = IssueJQL(project="DEV", assignee_account_id="acc-001")
        self.mock_jira.search_issues.return_value = [_create_jira_issue("DEV-1")]

        # when
        result = self.jira_client.fetch_search_issues(jql)

        # then
        assert len(result) == 1
        self.mock_jira.search_issues.assert_called_once_with(
            jql.build(),
            expand="changelog",
            startAt=0,
            maxResults=50,
        )

    def test_fetch_search_issues_start_at과_max_results를_전달한다(self):
        # given
        jql = IssueJQL(project="DEV")
        self.mock_jira.search_issues.return_value = []

        # when
        self.jira_client.fetch_search_issues(jql, start_at=10, max_results=20)

        # then
        self.mock_jira.search_issues.assert_called_once_with(
            jql.build(),
            expand="changelog",
            startAt=10,
            maxResults=20,
        )

    def test_fetch_search_issues_결과가_없으면_빈_리스트를_반환한다(self):
        # given
        jql = IssueJQL(project="DEV")
        self.mock_jira.search_issues.return_value = []

        # when
        result = self.jira_client.fetch_search_issues(jql)

        # then
        assert len(result) == 0

    # -- fetch_issue --

    def test_fetch_issue_이슈_키로_단건_조회한다(self):
        # given
        self.mock_jira.issue.return_value = _create_jira_issue("DEV-123", "버그 수정")

        # when
        result = self.jira_client.fetch_issue("DEV-123")

        # then
        assert result.key == "DEV-123"
        self.mock_jira.issue.assert_called_once_with("DEV-123")
