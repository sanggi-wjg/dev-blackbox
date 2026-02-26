import logging
import sys
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from dev_blackbox.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_REPOSITORY_SUFFIX = "Repository"
_MAX_FRAME_DEPTH = 30


def _extract_repository_comment() -> str | None:
    """호출 스택에서 Repository 클래스와 메서드명을 추출한다."""
    frame = sys._getframe(1)  # noqa: SLF001
    for _ in range(_MAX_FRAME_DEPTH):
        if frame is None:
            break
        local_self = frame.f_locals.get("self")
        if local_self is not None:
            cls_name = type(local_self).__name__
            if cls_name.endswith(_REPOSITORY_SUFFIX):
                return f"{cls_name}.{frame.f_code.co_name}"
        frame = frame.f_back
    return None


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


@event.listens_for(engine, "before_cursor_execute", retval=True)
def _add_query_comment(_conn, _cursor, statement, parameters, _context, _executemany):
    """실행되는 SQL에 Repository 출처를 코멘트로 추가한다."""
    comment = _extract_repository_comment()
    if comment:
        statement = f"/* {comment} */ {statement}"
    return statement, parameters


session_factory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 의존성 주입 목적
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


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    서비스 구현 로직 사용 목적
    ⚠️ 자동으로 트랜잭션의 commit, rollback 처리

    with get_db_session() as db:
        ...
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
