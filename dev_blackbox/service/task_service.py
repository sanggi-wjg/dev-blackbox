from sqlalchemy.orm import Session

from dev_blackbox.core.exception import TaskNotFoundException
from dev_blackbox.service.command.task_command import (
    CreateTaskCommand,
    DeleteTaskCommand,
    ReorderTasksCommand,
    UpdateTaskCommand,
)
from dev_blackbox.service.query.task_query import TaskQuery
from dev_blackbox.storage.rds.entity.task import Task
from dev_blackbox.storage.rds.repository.task_repository import TaskRepository


class TaskService:

    def __init__(self, session: Session):
        self.task_repository = TaskRepository(session)

    def get_tasks(self, query: TaskQuery) -> list[Task]:
        return self.task_repository.find_all_by_user_id_and_filters(
            query.user_id,
            query.statuses,
            query.is_archived,
        )

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

    def update_task(self, command: UpdateTaskCommand) -> Task:
        task = self.task_repository.find_by_id_and_user_id(command.task_id, command.user_id)
        if task is None:
            raise TaskNotFoundException(command.task_id)

        task.update(
            title=command.title,
            content=command.content,
            tags=command.tags,
            status=command.status,
            display_order=command.display_order,
        )
        self.task_repository.save(task)
        return task

    def reorder_tasks(self, command: ReorderTasksCommand) -> list[Task]:
        tasks = self.task_repository.find_all_by_ids_and_user_id(command.task_ids, command.user_id)
        task_map = {task.id: task for task in tasks}

        for order, task_id in enumerate(command.task_ids):
            task = task_map.get(task_id)
            if task is not None:
                task.display_order = order

        return sorted(tasks, key=lambda t: t.display_order)

    def delete_task(self, command: DeleteTaskCommand) -> None:
        self.task_repository.delete_by_id_and_user_id(command.task_id, command.user_id)
