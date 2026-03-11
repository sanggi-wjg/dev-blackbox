import logging
from functools import lru_cache

from jira import JIRA, Issue, User
from jira.client import ResultList
from jira.exceptions import JIRAError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

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
        logger.info(f"JiraClient 생성: server={server}")
        return cls(server, username, api_token)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(),
        retry=retry_if_exception_type((JIRAError,)),
    )
    def fetch_assignable_users(self, project: str) -> ResultList[User]:
        logger.info(f"할당 가능 사용자 조회: project={project}")
        return self.jira.search_assignable_users_for_projects("", projectKeys=project)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(),
        retry=retry_if_exception_type((JIRAError,)),
    )
    def fetch_search_issues(
        self,
        jql: IssueJQL,
        start_at: int = 0,
        max_results: int = 50,
    ) -> ResultList[Issue]:
        query = jql.build()
        logger.info(f"이슈 조회: jql_query={query}, start_at={start_at}, max_results={max_results}")
        return self.jira.search_issues(
            query,
            expand="changelog",
            startAt=start_at,
            maxResults=max_results,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(),
        retry=retry_if_exception_type((JIRAError,)),
    )
    def fetch_issue(self, issue_key: str) -> Issue:
        logger.info(f"이슈 단건 조회: issue_key={issue_key}")
        return self.jira.issue(issue_key)


@lru_cache(maxsize=10)
def get_jira_client(server: str, username: str, api_token: str) -> JiraClient:
    return JiraClient.create(server, username, api_token)
