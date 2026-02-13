import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from dev_blackbox.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


engine = create_engine(
    url=settings.database.dsn,
    pool_size=settings.database.pool_size,  # 풀에 유지할 연결 수
    max_overflow=settings.database.max_overflow,  # pool_size 초과 시 추가 허용 수
    pool_timeout=settings.database.pool_timeout,  # 연결 대기 타임아웃 (초)
    pool_recycle=settings.database.pool_recycle,  # 연결 재생성 주기 (초)
    pool_pre_ping=settings.database.pool_pre_ping,  # 사용 전 연결 검증
    isolation_level=settings.database.isolation_level,
    echo=settings.database.debug,
    echo_pool=settings.database.debug,
)
session_factory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성 주입 목적
    ⚠️ endpoint 로직에서 트랜잭션의 commit, rollback 처리 필요
    """
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    일반 서비스 로직 사용 목적
    ⚠️ 자동으로 트랜잭션의 commit, rollback 처리
    """
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Exception occurred during database transaction.")
        raise
    finally:
        db.close()
