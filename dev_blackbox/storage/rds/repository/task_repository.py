from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.core.enum import TaskStatusEnum
from dev_blackbox.storage.rds.entity.task import Task


class TaskRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: Task) -> Task:
        self.session.add(entity)
        self.session.flush()
        return entity

    def find_by_id_and_user_id(self, entity_id: int, user_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == entity_id, Task.user_id == user_id)
        return self.session.scalar(stmt)

    def delete_by_id_and_user_id(self, entity_id: int, user_id: int) -> None:
        stmt = delete(Task).where(Task.id == entity_id, Task.user_id == user_id)
        self.session.execute(stmt)

    def find_all_by_ids_and_user_id(self, entity_ids: list[int], user_id: int) -> list[Task]:
        stmt = select(Task).where(Task.id.in_(entity_ids), Task.user_id == user_id)
        return list(self.session.scalars(stmt))

    def find_all_by_user_id(self, user_id: int) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.display_order.asc(), Task.id.asc())
        )
        return list(self.session.scalars(stmt))

    def find_all_by_user_id_and_filters(
        self,
        user_id: int,
        statuses: list[TaskStatusEnum] | None = None,
        is_archived: bool = False,
    ) -> list[Task]:
        stmt = select(Task).where(Task.user_id == user_id, Task.is_archived == is_archived)
        if statuses:
            stmt = stmt.where(Task.status.in_(statuses))
        stmt = stmt.order_by(Task.display_order.asc(), Task.id.asc())
        return list(self.session.scalars(stmt))
