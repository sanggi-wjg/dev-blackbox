from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser
from dev_blackbox.controller.config.security_config import get_current_admin_user
from dev_blackbox.core.database import get_db
from dev_blackbox.core.password import get_password_service
from dev_blackbox.storage.rds.entity import User
from main import app


@pytest.fixture()
def authenticated_admin_user(
    db_session: Session,
) -> AuthenticatedUser:
    password_service = get_password_service()
    user = User.create_admin(
        name="admin",
        email="admin@dev.com",
        hashed_password=password_service.hash("password"),
        timezone="Asia/Seoul",
    )
    db_session.add(user)
    db_session.flush()
    return AuthenticatedUser.from_entity(user)


@pytest.fixture(autouse=True)
def _override_dependencies(
    db_session: Session,
    authenticated_admin_user: AuthenticatedUser,
) -> Generator[None, None, None]:

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_admin_user] = lambda: authenticated_admin_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(
    client: TestClient,
) -> TestClient:
    client.headers = {"Authorization": "Bearer fake-token"}
    return client
