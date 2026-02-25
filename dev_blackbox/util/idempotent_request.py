import logging
from typing import Annotated

from fastapi import Header, Request

from dev_blackbox.core.cache import CacheService
from dev_blackbox.core.const import IDEMPOTENCY_PROCESSING_VALUE, IDEMPOTENCY_TTL_SECONDS
from dev_blackbox.core.exception import CompletedRequestException, ConflictRequestException

logger = logging.getLogger(__name__)


def _build_cache_key(request: Request, idempotency_key: str) -> str:
    request_path = request.url.path
    return f"idempotency:{request_path}:{idempotency_key}"


def idempotent_request(
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="Request ID for idempotency",
        ),
    ],
    request: Request,
) -> str:
    """
    1. nx=True로 Redis에 키 설정 시도 → 성공 시 PROCESSING 마킹 후 진행
    2. 실패 시 기존 키 값 확인:
       - PROCESSING → 진행 중, ConflictRequestException (409)
       - JSON 결과 → 완료됨, CompletedRequestException (422 + 캐시된 응답
    """
    cache_key = _build_cache_key(request, idempotency_key)

    try:
        cache_service = CacheService()
        is_acquired = cache_service.set(
            cache_key,
            IDEMPOTENCY_PROCESSING_VALUE,
            nx=True,
            ex=IDEMPOTENCY_TTL_SECONDS,
        )

        if not is_acquired:
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                if cached_value == IDEMPOTENCY_PROCESSING_VALUE:
                    raise ConflictRequestException(idempotency_key)

                raise CompletedRequestException(
                    idempotency_key=idempotency_key,
                    cached_response=cached_value,
                )
    except ConflictRequestException, CompletedRequestException:
        raise
    except Exception as e:
        logger.warning(f"Redis unavailable for idempotency check: {e}")

    return idempotency_key


def save_idempotent_response(
    request: Request,
    idempotency_key: str,
    response_data: dict,
) -> None:
    cache_key = _build_cache_key(request, idempotency_key)

    try:
        cache_service = CacheService()
        cache_service.set(
            cache_key,
            response_data,
            ex=IDEMPOTENCY_TTL_SECONDS,
        )
    except Exception as e:
        logger.warning(f"Failed to cache idempotent response: {e}")
