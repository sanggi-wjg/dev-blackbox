from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.model.user_search_condition import UserSearchCondition


class UserRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def find_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.is_deleted == False)
        return self.session.scalar(stmt)

    def find_all(self) -> list[User]:
        stmt = select(User).where(User.is_deleted == False).order_by(User.id)
        return list(self.session.scalars(stmt).all())

    def find_all_by_condition(self, condition: UserSearchCondition) -> list[User]:
        stmt = select(User).where(**condition.model_dump()).order_by(User.id)
        return list(self.session.scalars(stmt).all())

    def is_exist(self, user_id: int) -> bool:
        stmt = select(User.id).where(User.id == user_id, User.is_deleted == False)
        return self.session.scalar(stmt) is not None
