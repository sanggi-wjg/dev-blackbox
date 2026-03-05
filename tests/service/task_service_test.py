import pytest

from dev_blackbox.core.enum import TaskStatusEnum
from dev_blackbox.core.exception import TaskNotFoundException
from dev_blackbox.service.command.task_command import (
    CreateTaskCommand,
    DeleteTaskCommand,
    ReorderTasksCommand,
    UpdateTaskCommand,
)
from dev_blackbox.service.query.task_query import TaskQuery
from dev_blackbox.service.task_service import TaskService


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
