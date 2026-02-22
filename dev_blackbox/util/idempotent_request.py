import json
import logging
from typing import Annotated

from fastapi import Header, Request

from dev_blackbox.core.cache import get_redis_client
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
        redis_client = get_redis_client()
        is_acquired = redis_client.set(
            cache_key, IDEMPOTENCY_PROCESSING_VALUE, nx=True, ex=IDEMPOTENCY_TTL_SECONDS
        )

        if not is_acquired:
            cached_value: bytes = redis_client.get(cache_key)  # pyright: ignore
            if cached_value is not None:
                value = cached_value.decode()
                if value == IDEMPOTENCY_PROCESSING_VALUE:
                    raise ConflictRequestException(idempotency_key)

                raise CompletedRequestException(
                    idempotency_key=idempotency_key,
                    cached_response=json.loads(value),
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
        redis_client = get_redis_client()
        redis_client.set(
            cache_key,
            json.dumps(response_data, ensure_ascii=False),
            ex=IDEMPOTENCY_TTL_SECONDS,
        )
    except Exception as e:
        logger.warning(f"Failed to cache idempotent response: {e}")
