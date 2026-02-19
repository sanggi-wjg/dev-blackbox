from typing import Generator, Callable

import pytest
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from testcontainers.postgres import PostgresContainer

from dev_blackbox.storage.rds.entity import *  # noqa: F403,F401
from dev_blackbox.storage.rds.entity.base import Base


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    with PostgresContainer(
        image="pgvector/pgvector:pg17",
        port=7200,
    ) as postgres:
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
) -> Callable[[str], User]:

    def _create(email: str) -> User:
        user = User.create(name=email, email=email)
        db_session.add(user)
        db_session.flush()
        return user

    return _create
