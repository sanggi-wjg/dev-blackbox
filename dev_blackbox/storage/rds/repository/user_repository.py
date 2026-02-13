from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.user import User


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
