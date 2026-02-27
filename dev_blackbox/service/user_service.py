from sqlalchemy.orm import Session

from dev_blackbox.core.exception import UserNotFoundException
from dev_blackbox.core.jwt_handler import get_jwt_service
from dev_blackbox.core.password import get_password_service
from dev_blackbox.service.command.user_command import CreateUserCommand
from dev_blackbox.service.query.user_query import UserQuery
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository import UserRepository


class UserService:

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)
        self.password_service = get_password_service()
        self.jwt_service = get_jwt_service()

    def create_user(self, command: CreateUserCommand) -> User:
        hashed_password = self.password_service.hash_password(command.password)
        user = User.create(
            name=command.name,
            email=command.email,
            hashed_password=hashed_password,
            timezone=command.timezone,
        )
        return self.user_repository.save(user)

    def create_admin_user(self, command: CreateUserCommand) -> User:
        hashed_password = self.password_service.hash_password(command.password)
        user = User.create_admin(
            name=command.name,
            email=command.email,
            hashed_password=hashed_password,
            timezone=command.timezone,
        )
        return self.user_repository.save(user)

    def get_user_by_id_or_throw(self, user_id: int) -> User:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return user

    def get_user_by_email_or_none(self, email: str) -> User | None:
        return self.user_repository.find_by_email(email)

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.get_user_by_email_or_none(email)
        if user is None:
            return None

        is_valid_password = self.password_service.verify_password(password, user.password)
        if not is_valid_password:
            return None

        return user

    def create_jwt_token(self, user: User) -> str:
        payload = {
            "sub": user.email,
            "is_admin": user.is_admin,
        }
        return self.jwt_service.create_token(payload)

    def get_users(self) -> list[User]:
        return self.user_repository.find_all()

    def get_users_by_query(self, query: UserQuery) -> list[User]:
        return self.user_repository.find_all_by_condition(
            name=query.name,
            is_deleted=query.is_deleted,
        )

    def delete_user(self, user_id: int) -> None:
        user = self.get_user_by_id_or_throw(user_id)
        user.delete()
