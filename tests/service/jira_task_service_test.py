from typing import Callable
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.client.model.jira_api_model import IssueJQL, JiraIssueStatus
from dev_blackbox.service.jira_task_service import JiraTaskService
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.entity.task import Task
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository.task_repository import TaskRepository


class JiraTaskServiceTest:

    # ── sync_jira_backlog ──

    def test_sync_jira_backlog(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-sync-1",
        )

        # mock
        mock_issue = MagicMock()
        mock_issue.id = "10001"
        mock_issue.key = "PROJ-1"
        mock_issue.fields.summary = "백로그 이슈"
        mock_issue.fields.description = "이슈 설명"

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = [mock_issue]

        mocker.patch(
            "dev_blackbox.service.jira_task_service.get_jira_client",
            return_value=mock_client,
        )

        service = JiraTaskService(db_session)

        # when
        service.sync_jira_backlog()

        # then
        task_repo = TaskRepository(db_session)
        tasks = task_repo.find_all_has_jira_issue_key(user_id=user.id)
        assert len(tasks) == 1
        assert tasks[0].jira_issue_id == mock_issue.id
        assert tasks[0].jira_issue_key == mock_issue.key
        assert tasks[0].title == mock_issue.fields.summary
        assert tasks[0].content == mock_issue.fields.description
        assert tasks[0].jira_issue_url == f"{secret.url}/browse/{mock_issue.key}"
        mock_client.fetch_search_issues.assert_called_once()

    def test_sync_jira_backlog_기존_태스크_key는_제외(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-sync-2",
        )

        existing_task = Task.create_from_jira(
            user_id=user.id,
            title="기존 태스크",
            display_order=0,
            jira_issue_id="10000",
            jira_issue_key="PROJ-EXIST",
            jira_issue_url=f"{secret.url}/browse/PROJ-EXIST",
        )
        db_session.add(existing_task)
        db_session.flush()

        # mock
        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = []

        mocker.patch(
            "dev_blackbox.service.jira_task_service.get_jira_client",
            return_value=mock_client,
        )

        service = JiraTaskService(db_session)

        # when
        service.sync_jira_backlog()

        # then
        call_args = mock_client.fetch_search_issues.call_args
        jql = call_args[0][0]
        assert isinstance(jql, IssueJQL)
        assert jql.exclude_keys == [existing_task.jira_issue_key]
        assert jql.project == jira_user.project
        assert jql.assignee_account_id == jira_user.account_id
        assert jql.include_statuses == [JiraIssueStatus.BACKLOG]

    def test_sync_jira_backlog_백로그_이슈_없으면_태스크_미생성(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-sync-3",
        )

        # mock
        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = []

        mocker.patch(
            "dev_blackbox.service.jira_task_service.get_jira_client",
            return_value=mock_client,
        )

        service = JiraTaskService(db_session)

        # when
        service.sync_jira_backlog()

        # then
        task_repo = TaskRepository(db_session)
        tasks = task_repo.find_all_has_jira_issue_key(user_id=user.id)
        assert tasks == []

    def test_sync_jira_backlog_여러_이슈_동기화(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-sync-4",
        )

        # mock
        mock_issue_1 = MagicMock()
        mock_issue_1.id = "10001"
        mock_issue_1.key = "PROJ-1"
        mock_issue_1.fields.summary = "첫 번째 이슈"
        mock_issue_1.fields.description = "설명 1"

        mock_issue_2 = MagicMock()
        mock_issue_2.id = "10002"
        mock_issue_2.key = "PROJ-2"
        mock_issue_2.fields.summary = "두 번째 이슈"
        mock_issue_2.fields.description = "설명 2"

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = [mock_issue_1, mock_issue_2]

        mocker.patch(
            "dev_blackbox.service.jira_task_service.get_jira_client",
            return_value=mock_client,
        )

        service = JiraTaskService(db_session)

        # when
        service.sync_jira_backlog()

        # then
        task_repo = TaskRepository(db_session)
        tasks = task_repo.find_all_has_jira_issue_key(user_id=user.id)
        assert len(tasks) == 2
        keys = {t.jira_issue_key for t in tasks}
        assert keys == {mock_issue_1.key, mock_issue_2.key}

    def test_sync_jira_backlog_display_order가_순서대로_설정(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-sync-5",
        )

        # mock
        mock_issues = []
        for i in range(3):
            issue = MagicMock()
            issue.id = str(10001 + i)
            issue.key = f"PROJ-{i + 1}"
            issue.fields.summary = f"이슈 {i + 1}"
            issue.fields.description = ""
            mock_issues.append(issue)

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = mock_issues

        mocker.patch(
            "dev_blackbox.service.jira_task_service.get_jira_client",
            return_value=mock_client,
        )

        service = JiraTaskService(db_session)

        # when
        service.sync_jira_backlog()

        # then
        task_repo = TaskRepository(db_session)
        tasks = task_repo.find_all_has_jira_issue_key(user_id=user.id)
        tasks_sorted = sorted(tasks, key=lambda t: t.display_order)
        for i, task in enumerate(tasks_sorted):
            assert task.display_order == i

    def test_sync_jira_backlog_jira_사용자가_없으면_동기화_안함(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user_fixture()

        mock_client = MagicMock(spec=JiraClient)
        mocker.patch(
            "dev_blackbox.service.jira_task_service.get_jira_client",
            return_value=mock_client,
        )

        service = JiraTaskService(db_session)

        # when
        service.sync_jira_backlog()

        # then
        mock_client.fetch_search_issues.assert_not_called()
