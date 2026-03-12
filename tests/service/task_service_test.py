from unittest.mock import MagicMock

import pytest

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.core.enum import TaskStatusEnum
from dev_blackbox.core.exception import TaskNotFoundException, UserNotFoundException
from dev_blackbox.service.command.task_command import (
    ArchiveTaskCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    ReorderTasksCommand,
    SyncJiraTaskCommand,
    UnarchiveTaskCommand,
    UpdateTaskCommand,
)
from dev_blackbox.service.query.task_query import TaskQuery
from dev_blackbox.service.task_service import TaskService
from dev_blackbox.storage.rds.entity.task import Task


class TaskServiceTest:

    def test_get_tasks(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-list@dev.com")
        task1 = task_fixture(user_id=user.id, title="태스크1", display_order=0)
        task2 = task_fixture(user_id=user.id, title="태스크2", display_order=1)

        service = TaskService(db_session)
        query = TaskQuery(user_id=user.id)

        # when
        result = service.get_tasks(query)

        # then
        assert result == [task1, task2]

    def test_get_tasks_빈_결과(self, db_session, user_fixture):
        # given
        user = user_fixture("task-empty@dev.com")
        service = TaskService(db_session)
        query = TaskQuery(user_id=user.id)

        # when
        result = service.get_tasks(query)

        # then
        assert result == []

    def test_get_tasks_상태_필터링(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-filter@dev.com")
        todo_task = task_fixture(user_id=user.id, title="할일", status=TaskStatusEnum.TODO)
        task_fixture(user_id=user.id, title="완료", status=TaskStatusEnum.DONE)

        service = TaskService(db_session)
        query = TaskQuery(user_id=user.id, statuses=[TaskStatusEnum.TODO])

        # when
        result = service.get_tasks(query)

        # then
        assert result == [todo_task]

    def test_create_task(self, db_session, user_fixture):
        # given
        user = user_fixture("task-create@dev.com")
        service = TaskService(db_session)
        command = CreateTaskCommand(
            user_id=user.id,
            title="새 태스크",
            status=TaskStatusEnum.TODO,
            content="태스크 내용",
            tags="python,test",
            display_order=0,
        )

        # when
        result = service.create_task(command)

        # then
        assert result.id is not None
        assert result.title == command.title
        assert result.content == command.content
        assert result.tags == command.tags
        assert result.status == command.status
        assert result.user_id == command.user_id

    def test_update_task(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-update@dev.com")
        task = task_fixture(user_id=user.id, title="원래 제목")

        service = TaskService(db_session)
        command = UpdateTaskCommand(
            task_id=task.id,
            user_id=user.id,
            title="수정된 제목",
            content="수정된 내용",
            tags="updated",
            status=TaskStatusEnum.IN_PROGRESS,
            display_order=1,
        )

        # when
        result = service.update_task(command)

        # then
        assert result.title == command.title
        assert result.content == command.content
        assert result.tags == command.tags
        assert result.status == command.status
        assert result.display_order == command.display_order

    def test_update_task_존재하지_않으면_예외(self, db_session, user_fixture):
        # given
        user = user_fixture("task-update-err@dev.com")
        service = TaskService(db_session)
        command = UpdateTaskCommand(
            task_id=9999,
            user_id=user.id,
            title="제목",
            content="내용",
            tags=None,
            status=TaskStatusEnum.TODO,
            display_order=0,
        )

        # when & then
        with pytest.raises(TaskNotFoundException):
            service.update_task(command)

    def test_reorder_tasks(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-reorder@dev.com")
        task1 = task_fixture(user_id=user.id, title="첫번째", display_order=0)
        task2 = task_fixture(user_id=user.id, title="두번째", display_order=1)
        task3 = task_fixture(user_id=user.id, title="세번째", display_order=2)

        service = TaskService(db_session)
        command = ReorderTasksCommand(
            user_id=user.id,
            task_ids=[task3.id, task1.id, task2.id],
        )

        # when
        result = service.reorder_tasks(command)

        # then
        assert result == [task3, task1, task2]
        assert task3.display_order == 0
        assert task1.display_order == 1
        assert task2.display_order == 2

    def test_delete_task(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-delete@dev.com")
        task = task_fixture(user_id=user.id, title="삭제 대상")

        service = TaskService(db_session)

        command = DeleteTaskCommand(task_id=task.id, user_id=user.id)

        # when
        service.delete_task(command)

        # then
        query = TaskQuery(user_id=user.id)
        result = service.get_tasks(query)
        assert task not in result

    def test_archive_task(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-archive@dev.com")
        task = task_fixture(user_id=user.id, title="아카이브 대상")

        service = TaskService(db_session)
        command = ArchiveTaskCommand(task_id=task.id, user_id=user.id)

        # when
        result = service.archive_task(command)

        # then
        assert result.is_archived is True
        assert result.archived_at is not None

    def test_archive_task_존재하지_않으면_예외(self, db_session, user_fixture):
        # given
        user = user_fixture("task-archive-err@dev.com")
        service = TaskService(db_session)
        command = ArchiveTaskCommand(task_id=9999, user_id=user.id)

        # when & then
        with pytest.raises(TaskNotFoundException):
            service.archive_task(command)

    def test_unarchive_task(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-unarchive@dev.com")
        task = task_fixture(user_id=user.id, title="언아카이브 대상")
        task.archive()
        db_session.flush()

        service = TaskService(db_session)
        command = UnarchiveTaskCommand(task_id=task.id, user_id=user.id)

        # when
        result = service.unarchive_task(command)

        # then
        assert result.is_archived is False

    def test_unarchive_task_존재하지_않으면_예외(self, db_session, user_fixture):
        # given
        user = user_fixture("task-unarchive-err@dev.com")
        service = TaskService(db_session)
        command = UnarchiveTaskCommand(task_id=9999, user_id=user.id)

        # when & then
        with pytest.raises(TaskNotFoundException):
            service.unarchive_task(command)

    def test_get_tasks_아카이브된_태스크는_기본_조회에서_제외(
        self, db_session, user_fixture, task_fixture
    ):
        # given
        user = user_fixture("task-archive-filter@dev.com")
        active_task = task_fixture(user_id=user.id, title="활성 태스크")
        archived_task = task_fixture(user_id=user.id, title="아카이브 태스크")
        archived_task.archive()
        db_session.flush()

        service = TaskService(db_session)
        query = TaskQuery(user_id=user.id)

        # when
        result = service.get_tasks(query)

        # then
        assert active_task in result
        assert archived_task not in result

    def test_get_tasks_아카이브된_태스크만_조회(self, db_session, user_fixture, task_fixture):
        # given
        user = user_fixture("task-archive-only@dev.com")
        task_fixture(user_id=user.id, title="활성 태스크")
        archived_task = task_fixture(user_id=user.id, title="아카이브 태스크")
        archived_task.archive()
        db_session.flush()

        service = TaskService(db_session)
        query = TaskQuery(user_id=user.id, is_archived=True)

        # when
        result = service.get_tasks(query)

        # then
        assert result == [archived_task]

    def test_sync_to_jira(
        self, mocker, db_session, user_fixture, jira_secret_fixture, jira_user_fixture
    ):
        # given
        user = user_fixture("task-sync-jira@dev.com")
        jira_secret = jira_secret_fixture()
        jira_user_fixture(jira_secret_id=jira_secret.id, user_id=user.id)

        task = Task.create_from_jira(
            user_id=user.id,
            title="Jira 태스크",
            display_order=0,
            jira_issue_id="10001",
            jira_issue_key="PROJ-1",
            jira_issue_url="https://test.atlassian.net/browse/PROJ-1",
            content="태스크 설명 내용",
        )
        db_session.add(task)
        db_session.flush()

        service = TaskService(db_session)
        command = SyncJiraTaskCommand(task_id=task.id, user_id=user.id)

        # mock
        mock_client = MagicMock(spec=JiraClient)
        mocker.patch(
            "dev_blackbox.service.task_service.get_jira_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_to_jira(command)

        # then
        assert result.jira_synced_at is not None
        mock_client.update_issue_description.assert_called_once_with(
            issue_key=task.jira_issue_key,
            description=task.content,
        )

    def test_sync_to_jira_태스크가_존재하지_않으면_예외(self, db_session, user_fixture):
        # given
        user = user_fixture("task-sync-notfound@dev.com")
        service = TaskService(db_session)
        command = SyncJiraTaskCommand(task_id=9999, user_id=user.id)

        # when & then
        with pytest.raises(TaskNotFoundException):
            service.sync_to_jira(command)

    def test_sync_to_jira_Jira_연동_정보_없으면_API_호출_안함(
        self, mocker, db_session, user_fixture, task_fixture
    ):
        # given
        user = user_fixture("task-sync-nojira@dev.com")
        task = task_fixture(user_id=user.id, title="일반 태스크", content="내용")

        service = TaskService(db_session)
        command = SyncJiraTaskCommand(task_id=task.id, user_id=user.id)

        # mock
        mock_get_jira_client = mocker.patch(
            "dev_blackbox.service.task_service.get_jira_client",
        )

        # when
        result = service.sync_to_jira(command)

        # then
        assert result == task
        mock_get_jira_client.assert_not_called()

    def test_sync_to_jira_content가_비어있으면_API_호출_안함(
        self, mocker, db_session, user_fixture
    ):
        # given
        user = user_fixture("task-sync-nocontent@dev.com")
        task = Task.create_from_jira(
            user_id=user.id,
            title="Jira 태스크",
            display_order=0,
            jira_issue_id="10002",
            jira_issue_key="PROJ-2",
            jira_issue_url="https://test.atlassian.net/browse/PROJ-2",
            content="",
        )
        db_session.add(task)
        db_session.flush()

        service = TaskService(db_session)
        command = SyncJiraTaskCommand(task_id=task.id, user_id=user.id)

        # mock
        mock_get_jira_client = mocker.patch(
            "dev_blackbox.service.task_service.get_jira_client",
        )

        # when
        result = service.sync_to_jira(command)

        # then
        assert result == task
        mock_get_jira_client.assert_not_called()

    def test_sync_to_jira_User가_존재하지_않으면_예외(self, mocker, db_session):
        # given
        # user_id=9999로 Task를 직접 생성 (FK 제약 우회를 위해 flush하지 않음)
        task = Task.create_from_jira(
            user_id=9999,
            title="Jira 태스크",
            display_order=0,
            jira_issue_id="10003",
            jira_issue_key="PROJ-3",
            jira_issue_url="https://test.atlassian.net/browse/PROJ-3",
            content="태스크 설명",
        )
        # TaskRepository.find_by_id_and_user_id를 mock하여 FK 제약 회피
        mocker.patch.object(
            TaskService,
            "_get_task_or_throw",
            return_value=task,
        )

        service = TaskService(db_session)
        command = SyncJiraTaskCommand(task_id=1, user_id=9999)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.sync_to_jira(command)

    def test_sync_to_jira_JiraUser가_할당되지_않으면_API_호출_안함(
        self, mocker, db_session, user_fixture
    ):
        # given
        user = user_fixture("task-sync-nojirauser@dev.com")
        task = Task.create_from_jira(
            user_id=user.id,
            title="Jira 태스크",
            display_order=0,
            jira_issue_id="10004",
            jira_issue_key="PROJ-4",
            jira_issue_url="https://test.atlassian.net/browse/PROJ-4",
            content="태스크 설명",
        )
        db_session.add(task)
        db_session.flush()

        service = TaskService(db_session)
        command = SyncJiraTaskCommand(task_id=task.id, user_id=user.id)

        # mock
        mock_get_jira_client = mocker.patch(
            "dev_blackbox.service.task_service.get_jira_client",
        )

        # when
        result = service.sync_to_jira(command)

        # then
        assert result == task
        mock_get_jira_client.assert_not_called()
