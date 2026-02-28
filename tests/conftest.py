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
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.core.password import get_password_service
from dev_blackbox.storage.rds.entity import *  # noqa: F403,F401
from dev_blackbox.storage.rds.entity.base import Base
from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret
from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
from dev_blackbox.storage.rds.entity.slack_user import SlackUser
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
def jira_user_fixture(
    db_session: Session,
) -> Callable[..., JiraUser]:

    def _create(
        jira_secret_id: int,
        user_id: int | None = None,
        account_id: str = "test-account-id",
        display_name: str = "Test Jira User",
        email_address: str = "jira@dev.com",
        url: str = "https://test.atlassian.net/user",
        project: str | None = None,
    ) -> JiraUser:
        jira_user = JiraUser.create(
            jira_secret_id=jira_secret_id,
            account_id=account_id,
            is_active=True,
            display_name=display_name,
            email_address=email_address,
            url=url,
            project=project,
            user_id=user_id,
        )
        db_session.add(jira_user)
        db_session.flush()
        return jira_user

    return _create


@pytest.fixture()
def jira_event_fixture(
    db_session: Session,
) -> Callable[..., JiraEvent]:

    def _create(
        user_id: int,
        jira_user_id: int,
        target_date: date = date(2025, 1, 1),
        issue_id: str = "10001",
        issue_key: str = "PROJ-1",
    ) -> JiraEvent:
        event = JiraEvent.create(
            user_id=user_id,
            jira_user_id=jira_user_id,
            target_date=target_date,
            issue_id=issue_id,
            issue_key=issue_key,
            issue={"id": issue_id, "key": issue_key, "fields": {}},
            changelog=None,
        )
        db_session.add(event)
        db_session.flush()
        return event

    return _create


@pytest.fixture()
def slack_user_fixture(
    db_session: Session,
) -> Callable[..., SlackUser]:

    def _create(
        slack_secret_id: int,
        user_id: int | None = None,
        member_id: str = "U_TEST_MEMBER",
        display_name: str = "Test Slack User",
        real_name: str = "Test User",
        email: str | None = "slack@dev.com",
    ) -> SlackUser:
        slack_user = SlackUser.create(
            slack_secret_id=slack_secret_id,
            member_id=member_id,
            is_active=True,
            display_name=display_name,
            real_name=real_name,
            email=email,
            user_id=user_id,
        )
        db_session.add(slack_user)
        db_session.flush()
        return slack_user

    return _create


@pytest.fixture()
def slack_message_fixture(
    db_session: Session,
) -> Callable[..., SlackMessage]:

    def _create(
        user_id: int,
        slack_user_id: int,
        target_date: date = date(2025, 1, 1),
        channel_id: str = "C_TEST",
        channel_name: str = "general",
        message_ts: str = "1735689600.000100",
        message_text: str = "Hello",
        thread_ts: str | None = None,
    ) -> SlackMessage:
        message = SlackMessage.create(
            user_id=user_id,
            slack_user_id=slack_user_id,
            target_date=target_date,
            channel_id=channel_id,
            channel_name=channel_name,
            message_ts=message_ts,
            message_text=message_text,
            message={"ts": message_ts, "text": message_text},
            thread_ts=thread_ts,
        )
        db_session.add(message)
        db_session.flush()
        return message

    return _create


@pytest.fixture()
def platform_work_log_fixture(
    db_session: Session,
) -> Callable[..., PlatformWorkLog]:

    def _create(
        user_id: int,
        target_date: date = date(2025, 1, 1),
        platform: PlatformEnum = PlatformEnum.GITHUB,
        content: str = "Test content",
        model_name: str = "test-model",
        prompt: str = "test-prompt",
    ) -> PlatformWorkLog:
        work_log = PlatformWorkLog.create(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
            content=content,
            model_name=model_name,
            prompt=prompt,
        )
        db_session.add(work_log)
        db_session.flush()
        return work_log

    return _create


@pytest.fixture()
def daily_work_log_fixture(
    db_session: Session,
) -> Callable[..., DailyWorkLog]:

    def _create(
        user_id: int,
        target_date: date = date(2025, 1, 1),
        content: str = "Daily summary",
    ) -> DailyWorkLog:
        work_log = DailyWorkLog.create(
            user_id=user_id,
            target_date=target_date,
            content=content,
        )
        db_session.add(work_log)
        db_session.flush()
        return work_log

    return _create


@pytest.fixture(scope="session", autouse=True)
def fake_redis() -> Generator[Redis, None, None]:
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server)

    get_redis_client.cache_clear()
    with patch("dev_blackbox.core.cache.get_redis_client", return_value=client):
        yield client
    get_redis_client.cache_clear()


@pytest.fixture(autouse=True)
def _flush_fake_redis(fake_redis: Redis) -> None:
    fake_redis.flushall()
