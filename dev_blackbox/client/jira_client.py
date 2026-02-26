import logging
from functools import lru_cache

from jira import JIRA, Issue, User
from jira.client import ResultList

from dev_blackbox.client.model.jira_api_model import IssueJQL

logger = logging.getLogger(__name__)


class JiraClient:

    def __init__(
        self,
        server: str,
        username: str,
        api_token: str,
    ):
        self.jira = JIRA(server=server, basic_auth=(username, api_token))

    @classmethod
    def create(cls, server: str, username: str, api_token: str) -> "JiraClient":
        logger.debug(f"Creating JiraClient for server: {server}")
        return cls(server, username, api_token)

    def fetch_assignable_users(self, project: str) -> ResultList[User]:
        logger.info(f"Fetching assignable users for project: {project}")
        return self.jira.search_assignable_users_for_projects("", projectKeys=project)

    def fetch_search_issues(
        self,
        jql: IssueJQL,
        start_at: int = 0,
        max_results: int = 50,
    ) -> ResultList[Issue]:
        logger.info(
            f"Fetching issues by jql: {jql}, start_at: {start_at}, max_results: {max_results}"
        )
        return self.jira.search_issues(
            jql.build(),
            expand="changelog",
            startAt=start_at,
            maxResults=max_results,
        )

    def fetch_issue(self, issue_key: str) -> Issue:
        logger.info(f"Fetching issue: {issue_key}")
        return self.jira.issue(issue_key)


@lru_cache(maxsize=10)
def get_jira_client(server: str, username: str, api_token: str) -> JiraClient:
    return JiraClient.create(server, username, api_token)
