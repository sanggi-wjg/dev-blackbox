import logging
from contextlib import contextmanager
from typing import Generator

from dev_blackbox.core.cache import get_redis_client, DistributedLockName

logger = logging.getLogger(__name__)


@contextmanager
def distributed_lock(
    lock_name: DistributedLockName,
    timeout: int = 60,
    blocking_timeout: int = 0,
) -> Generator[bool, None, None]:
    """
    Args:
        lock_name: 락 이름
        timeout: 락 자동 해제 시간 (초). 데드락 방지를 위해 필수 설정.
                 태스크 예상 실행 시간보다 충분히 길게 설정할 것.
        blocking_timeout: 락 획득 대기 시간 (초).
                         0이면 즉시 반환 (non-blocking),
                         양수면 해당 시간만큼 락 획득을 기다림.

    Yields:
        bool: 락 획득 성공 여부

    Example:
        with distributed_lock(DistributedLockName.COLLECT_PLATFORM_TASK, timeout=300) as acquired:
            if not acquired:
                logger.warning("Task is already running, skipping...")
                return
            # 락 획득 성공, 작업 수행
            do_work()
    """
    redis_client = get_redis_client()
    lock_key = f"lock:{lock_name.value}"
    lock = redis_client.lock(
        lock_key,
        timeout=timeout,
        blocking_timeout=blocking_timeout,
    )

    # 락 획득 시도 — acquire만 try로 감싸서 태스크 본문 예외와 분리
    acquired = False
    try:
        acquired = lock.acquire(blocking=blocking_timeout > 0)
    except Exception as e:
        logger.exception(f"Error acquiring lock {lock_key}: {e}")
        yield False
        return

    if acquired:
        logger.debug(f"Lock acquired: {lock_key}")
    else:
        logger.info(f"Failed to acquire lock (already held): {lock_key}")

    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock.release()
                logger.debug(f"Lock released: {lock_key}")
            except Exception as e:
                # 이미 만료되었거나 다른 이유로 해제 실패
                logger.warning(f"Failed to release lock {lock_key}: {e}")
