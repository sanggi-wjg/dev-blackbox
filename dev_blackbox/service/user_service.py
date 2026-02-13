from sqlalchemy.orm import Session

from dev_blackbox.controller.dto.user_dto import CreateUserRequestDto
from dev_blackbox.core.exception import UserByIdNotFoundException
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository import UserRepository


class UserService:

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)

    def create_user(self, request: CreateUserRequestDto) -> User:
        user = User.create(name=request.name, email=request.email)
        return self.user_repository.save(user)

    def get_user(self, user_id: int) -> User:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)
        return user

    def get_users(self) -> list[User]:
        return self.user_repository.find_all()
