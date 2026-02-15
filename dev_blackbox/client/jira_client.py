from functools import lru_cache

from jira import JIRA, Issue, User
from jira.client import ResultList

from dev_blackbox.core.config import get_settings


class JiraClient:
    """
    TODO
     - Jira jql db 등으로 옮기자
    """

    def __init__(
        self,
        server: str,
        username: str,
        api_token: str,
    ):
        self.jira = JIRA(server=server, basic_auth=(username, api_token))

    def fetch_assignable_users(self, project: str = "FMP") -> ResultList[User]:
        return self.jira.search_assignable_users_for_projects("", projectKeys=project)

    def fetch_search_issues(
        self,
        project: str = "FMP",
        start_at: int = 0,
        max_results: int = 50,
    ) -> ResultList[Issue]:
        jql = f"project = {project} AND assignee = 712020:f42eedc7-eae3-493b-a36a-2a2a6ef38f8c AND status != Closed AND updatedDate >= -30d ORDER BY created DESC"
        return self.jira.search_issues(
            jql, expand="changelog", startAt=start_at, maxResults=max_results
        )

    def fetch_issue(self, issue_key: str) -> Issue:
        return self.jira.issue(issue_key)


@lru_cache
def get_jira_client():
    jira_secrets = get_settings().jira
    return JiraClient(
        server=jira_secrets.url,
        username=jira_secrets.username,
        api_token=jira_secrets.api_token,
    )
