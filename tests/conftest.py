from typing import Generator, Callable

import pytest
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session

from dev_blackbox.core.config import get_settings
from dev_blackbox.storage.rds.entity import *  # noqa: F403,F401
from dev_blackbox.storage.rds.entity.base import Base


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    settings = get_settings()
    db = settings.database

    engine = create_engine(url=db.dsn, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db"),
            {"db": db.test_database},
        )
        if not result.fetchone():
            conn.execute(text(f"CREATE DATABASE {db.test_database}"))
    engine.dispose()
    del engine

    engine = create_engine(
        url=db.test_dsn,
        isolation_level=db.isolation_level,
        pool_pre_ping=True,
        echo=True,
        echo_pool=True,
    )
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine
    engine.dispose()
    del engine


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
