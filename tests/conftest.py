import uuid
from datetime import date
from typing import Generator, Callable
from unittest.mock import patch

import fakeredis
import pytest
from redis import Redis
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from testcontainers.postgres import PostgresContainer

from dev_blackbox.core.cache import get_redis_client
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.password import get_password_service
from dev_blackbox.storage.rds.entity import *  # noqa: F403,F401
from dev_blackbox.storage.rds.entity.base import Base
from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
from tests.fixtures.github_fixture import create_github_event_model


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    with PostgresContainer(image="pgvector/pgvector:pg17") as postgres:
        engine = create_engine(
            url=postgres.get_connection_url(),
            isolation_level="REPEATABLE READ",
        )
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

        Base.metadata.create_all(bind=engine)

        yield engine
        engine.dispose()


@pytest.fixture(scope="session")
def db_session_factory(
    test_engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=True,
    )


@pytest.fixture()
def db_session(
    db_session_factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture()
def user_fixture(
    db_session: Session,
) -> Callable[..., User]:

    def _create(
        email: str = "user@dev.com",
        password: str = "password",
    ) -> User:
        password_service = get_password_service()
        user = User.create(
            name=email,
            email=email,
            hashed_password=password_service.hash(password),
            timezone="Asia/Seoul",
        )
        db_session.add(user)
        db_session.flush()
        return user

    return _create


@pytest.fixture()
def github_user_secret_fixture(
    db_session: Session,
) -> Callable[..., GitHubUserSecret]:

    def _create(
        user_id: int,
        username: str = "test_user",
        personal_access_token: str = "token",
    ) -> GitHubUserSecret:
        encrypt_service = get_encrypt_service()
        secret = GitHubUserSecret.create(
            username=username,
            personal_access_token=encrypt_service.encrypt(personal_access_token),
            user_id=user_id,
        )
        db_session.add(secret)
        db_session.flush()
        return secret

    return _create


@pytest.fixture()
def jira_secret_fixture(
    db_session: Session,
) -> Callable[..., JiraSecret]:

    def _create(
        name: str = "Test Jira",
        url: str = "https://test.atlassian.net",
        username: str = "jira_user",
        api_token: str = "jira_token",
    ) -> JiraSecret:
        encrypt_service = get_encrypt_service()
        secret = JiraSecret.create(
            name=name,
            url=url,
            username=encrypt_service.encrypt(username),
            api_token=encrypt_service.encrypt(api_token),
        )
        db_session.add(secret)
        db_session.flush()
        return secret

    return _create


@pytest.fixture()
def slack_secret_fixture(
    db_session: Session,
) -> Callable[..., SlackSecret]:

    def _create(
        name: str = "Test Slack",
        bot_token: str = "xoxb-test-token",
    ) -> SlackSecret:
        encrypt_service = get_encrypt_service()
        secret = SlackSecret.create(
            name=name,
            bot_token=encrypt_service.encrypt(bot_token),
        )
        db_session.add(secret)
        db_session.flush()
        return secret

    return _create


@pytest.fixture()
def github_event_fixture(
    db_session: Session,
) -> Callable[..., GitHubEvent]:

    def _create(
        user_id: int,
        github_user_secret_id: int,
        target_date: date = date(2025, 1, 1),
        event_id: str | None = None,
        event_type: str = "PushEvent",
    ) -> GitHubEvent:
        event = GitHubEvent.create(
            user_id=user_id,
            github_user_secret_id=github_user_secret_id,
            target_date=target_date,
            event=create_github_event_model(
                event_id or str(uuid.uuid4()),
                event_type,
            ),
            commit=None,
        )
        db_session.add(event)
        db_session.flush()
        return event

    return _create


@pytest.fixture()
def fake_redis() -> Generator[Redis, None, None]:
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server)

    get_redis_client.cache_clear()
    with patch("dev_blackbox.core.cache.get_redis_client", return_value=client):
        yield client
    get_redis_client.cache_clear()
