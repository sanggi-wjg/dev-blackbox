from unittest.mock import MagicMock, patch

import pytest
from redis import Redis

from dev_blackbox.core.exception import CompletedRequestException, ConflictRequestException
from dev_blackbox.util.idempotent_request import (
    _build_cache_key,
    idempotent_request,
    save_idempotent_response,
)


def _mock_request(path: str = "/api/v1/work-logs/manual-sync") -> MagicMock:
    request = MagicMock()
    request.url.path = path
    return request


class BuildCacheKeyTest:

    def test_요청_경로와_멱등성_키로_캐시_키를_생성한다(self):
        # given
        request = _mock_request("/api/v1/work-logs/manual-sync")
        idempotency_key = "abc-123"

        # when
        result = _build_cache_key(request, idempotency_key)

        # then
        assert result == "idempotency:/api/v1/work-logs/manual-sync:abc-123"


class IdempotentRequestTest:

    def test_최초_요청은_멱등성_키를_반환한다(self, fake_redis: Redis):
        # given
        request = _mock_request()
        idempotency_key = "first-request"

        # when
        result = idempotent_request(idempotency_key, request)

        # then
        assert result == idempotency_key

    def test_처리_중인_요청을_중복_호출하면_ConflictRequestException이_발생한다(
        self, fake_redis: Redis
    ):
        # given
        request = _mock_request()
        idempotency_key = "conflict-request"

        idempotent_request(idempotency_key, request)

        # when / then
        with pytest.raises(ConflictRequestException):
            idempotent_request(idempotency_key, request)

    def test_완료된_요청을_중복_호출하면_CompletedRequestException이_발생한다(
        self, fake_redis: Redis
    ):
        # given
        request = _mock_request()
        idempotency_key = "completed-request"
        cached_response = {"message": "이미 완료된 작업입니다."}

        idempotent_request(idempotency_key, request)
        save_idempotent_response(request, idempotency_key, cached_response)

        # when / then
        with pytest.raises(CompletedRequestException) as exc_info:
            idempotent_request(idempotency_key, request)

        assert exc_info.value.cached_response == cached_response

    def test_Redis_불가용_시_예외_없이_멱등성_키를_반환한다(self):
        # given
        request = _mock_request()
        idempotency_key = "redis-unavailable"
        mock_cache = MagicMock()
        mock_cache.set.side_effect = Exception("Connection refused")

        with patch("dev_blackbox.util.idempotent_request.CacheService", return_value=mock_cache):
            # when
            result = idempotent_request(idempotency_key, request)

        # then — graceful degradation: 예외 없이 진행
        assert result == idempotency_key


class SaveIdempotentResponseTest:

    def test_응답_데이터를_캐시에_저장한다(self, fake_redis: Redis):
        # given
        request = _mock_request()
        idempotency_key = "save-response"
        response_data = {"message": "작업이 완료되었습니다."}

        idempotent_request(idempotency_key, request)

        # when
        save_idempotent_response(request, idempotency_key, response_data)

        # then — 캐시에서 PROCESSING이 아닌 실제 응답으로 대체되어야 한다
        from dev_blackbox.core.cache import CacheService

        cache_service = CacheService(cache_client=fake_redis)
        cache_key = _build_cache_key(request, idempotency_key)
        cached_value = cache_service.get(cache_key)

        assert cached_value == response_data

    def test_Redis_불가용_시_예외가_전파되지_않는다(self):
        # given
        request = _mock_request()
        idempotency_key = "save-redis-unavailable"
        response_data = {"message": "작업이 완료되었습니다."}
        mock_cache = MagicMock()
        mock_cache.set.side_effect = Exception("Connection refused")

        # when / then — 예외 없이 정상 완료
        with patch("dev_blackbox.util.idempotent_request.CacheService", return_value=mock_cache):
            save_idempotent_response(request, idempotency_key, response_data)
