import logging

from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import get_jira_client
from dev_blackbox.client.model.jira_api_model import JiraIssueStatus, IssueJQL
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.storage.rds.entity import Task
from dev_blackbox.storage.rds.repository import UserRepository, TaskRepository

logger = logging.getLogger(__name__)


class JiraTaskService:

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)
        self.task_repository = TaskRepository(session)
        self.encrypt_service = get_encrypt_service()

    def sync_jira_backlog(self):
        users = self.user_repository.find_all_with_jira()

        for user in users:
            if user.jira_user is None:
                continue

            logger.info(f"Jira 백로그 동기화 시작: user_id={user.id}")
            jira_secret = user.jira_user.jira_secret
            jira_client = get_jira_client(
                jira_secret.url,
                self.encrypt_service.decrypt(jira_secret.username),
                self.encrypt_service.decrypt(jira_secret.api_token),
            )

            tasks = self.task_repository.find_all_has_jira_issue_key(user_id=user.id)
            exists_keys = [task.jira_issue_key for task in tasks if task.jira_issue_key]
            logger.info(
                f"Jira 백로그 동기화 - 기존 태스크 조회: user_id={user.id}, count={len(tasks)}, keys={exists_keys}"
            )

            backlog_issues = jira_client.fetch_search_issues(
                IssueJQL(
                    project=user.jira_user.project,
                    include_statuses=[JiraIssueStatus.BACKLOG],
                    assignee_account_id=user.jira_user.account_id,
                    exclude_keys=exists_keys,
                    order_by="createdDate DESC",
                )
            )
            if not backlog_issues:
                logger.info(f"Jira 백로그 동기화 - 백로그 이슈 없음: user_id={user.id}")
                continue

            new_tasks = [
                Task.create_from_jira(
                    user_id=user.id,
                    title=issue.fields.summary,
                    content=issue.fields.description,
                    display_order=i,
                    jira_issue_id=issue.id,
                    jira_issue_key=issue.key,
                    jira_issue_url=f"{jira_secret.url}/browse/{issue.key}",
                )
                for i, issue in enumerate(backlog_issues)
            ]
            logger.info(
                f"Jira 백로그 동기화 - 신규 태스크 생성: user_id={user.id}, count={len(new_tasks)}, keys={[task.jira_issue_key for task in new_tasks]}"
            )
            self.task_repository.save_all(new_tasks)
