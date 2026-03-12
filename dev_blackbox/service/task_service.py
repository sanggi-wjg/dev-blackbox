from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import get_jira_client
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import TaskNotFoundException, UserNotFoundException
from dev_blackbox.service.command.task_command import (
    CreateTaskCommand,
    DeleteTaskCommand,
    ReorderTasksCommand,
    UpdateTaskCommand,
    ArchiveTaskCommand,
    UnarchiveTaskCommand,
    SyncJiraTaskCommand,
)
from dev_blackbox.service.query.task_query import TaskQuery
from dev_blackbox.storage.rds.entity import Task
from dev_blackbox.storage.rds.repository import UserRepository
from dev_blackbox.storage.rds.repository.task_repository import TaskRepository


class TaskService:

    def __init__(self, session: Session):
        self.task_repository = TaskRepository(session)
        self.encrypt_service = get_encrypt_service()
        self.user_repository = UserRepository(session)

    def get_tasks(self, query: TaskQuery) -> list[Task]:
        return self.task_repository.find_all_by_user_id_and_filters(
            query.user_id,
            query.statuses,
            query.is_archived,
        )

    def _get_task_or_throw(self, task_id: int, user_id: int) -> Task:
        task = self.task_repository.find_by_id_and_user_id(task_id, user_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        return task

    def create_task(self, command: CreateTaskCommand) -> Task:
        task = Task.create(
            user_id=command.user_id,
            title=command.title,
            status=command.status,
            content=command.content,
            tags=command.tags,
            display_order=command.display_order,
        )
        return self.task_repository.save(task)

    def sync_to_jira(self, command: SyncJiraTaskCommand) -> Task:
        task = self._get_task_or_throw(command.task_id, command.user_id)
        if not task.is_synced_with_jira():
            return task
        if task.jira_issue_key is None or not task.content:
            return task

        user = self.user_repository.find_with_join_by_id(command.user_id)
        if user is None:
            raise UserNotFoundException(command.user_id)
        if user.jira_user is None:
            return task

        jira_secret = user.jira_user.jira_secret
        jira_client = get_jira_client(
            jira_secret.url,
            self.encrypt_service.decrypt(jira_secret.username),
            self.encrypt_service.decrypt(jira_secret.api_token),
        )
        jira_client.update_issue_description(
            issue_key=task.jira_issue_key,
            description=task.content,
        )
        task.sync_jira()
        return task

    def update_task(self, command: UpdateTaskCommand) -> Task:
        task = self._get_task_or_throw(command.task_id, command.user_id)
        return task.update(
            title=command.title,
            content=command.content,
            tags=command.tags,
            status=command.status,
            display_order=command.display_order,
        )

    def delete_task(self, command: DeleteTaskCommand) -> None:
        self.task_repository.delete_by_id_and_user_id(command.task_id, command.user_id)

    def reorder_tasks(self, command: ReorderTasksCommand) -> list[Task]:
        tasks = self.task_repository.find_all_by_ids_and_user_id(command.task_ids, command.user_id)
        task_map = {task.id: task for task in tasks}

        for order, task_id in enumerate(command.task_ids):
            task = task_map.get(task_id)
            if task is not None:
                task.display_order = order

        return sorted(tasks, key=lambda t: t.display_order)

    def archive_task(self, command: ArchiveTaskCommand) -> Task:
        task = self._get_task_or_throw(command.task_id, command.user_id)
        return task.archive()

    def unarchive_task(self, command: UnarchiveTaskCommand) -> Task:
        task = self._get_task_or_throw(command.task_id, command.user_id)
        return task.unarchive()
