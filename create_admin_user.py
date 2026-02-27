from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.command.user_command import CreateUserCommand
from dev_blackbox.service.user_service import UserService

with get_db_session() as session:
    user_service = UserService(session)
    user_service.create_admin_user(
        CreateUserCommand(
            name="admin",
            email="admin@dev.com",
            password="admin-password",
            timezone="Asia/Seoul",
        )
    )
