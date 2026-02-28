from unittest.mock import MagicMock

from redis import Redis

from dev_blackbox.core.cache import (
    CacheService,
    resolve_cache_key,
    cacheable,
    cache_put,
    cache_evict,
)
from dev_blackbox.core.const import CacheTTL, CacheKey


def test_resolve_cache_key():
    # given
    def iam_function(text: str, *args, **kwargs):
        return f"{text} / {args} / {kwargs}"

    key_template = "iam_function:text:{text}:args:{args}:kwargs:{kwargs}"

    # when
    key = resolve_cache_key(key_template, iam_function, "test", 1, 2, a=3, b=4)

    # then
    assert key == "iam_function:text:test:args:(1, 2):kwargs:{'a': 3, 'b': 4}"


def test_resolve_cache_key_2():
    # given
    def iam_function(text: str, *args, **kwargs):
        return f"{text} / {args} / {kwargs}"

    key_template = "iam_function:text"

    # when
    key = resolve_cache_key(key_template, iam_function, "test", 1, 2, a=3, b=4)

    # then
    assert key == "iam_function:text"


class CacheableTest:

    def test_cacheable_캐시_미스시_함수를_실행하고_결과를_캐시한다(self, fake_redis: Redis):
        # given
        user_id = 1
        target_date = "2025-01-01"
        expected_value = {"name": "test_user"}
        mock_fn = MagicMock(return_value=expected_value)

        @cacheable(key=CacheKey.WORK_LOG_PLATFORM, ttl=CacheTTL.DEFAULT)
        def get_work_log(user_id: int, target_date: str) -> dict:
            return mock_fn(user_id, target_date)

        expected_key = resolve_cache_key(
            CacheKey.WORK_LOG_PLATFORM, get_work_log, user_id, target_date
        )

        # when
        result = get_work_log(user_id, target_date)

        # then
        assert result == expected_value
        mock_fn.assert_called_once_with(user_id, target_date)
        assert fake_redis.exists(expected_key)

    def test_cacheable_캐시_히트시_함수를_실행하지_않고_캐시값을_반환한다(self, fake_redis: Redis):
        # given
        user_id = 1
        target_date = "2025-01-01"
        expected_value = {"name": "test_user"}
        call_count = MagicMock()

        @cacheable(key=CacheKey.WORK_LOG_PLATFORM, ttl=CacheTTL.DEFAULT)
        def get_work_log(user_id: int, target_date: str) -> dict:
            call_count()
            return expected_value

        get_work_log(user_id, target_date)  # 첫 호출 — 캐시 미스

        # when
        result = get_work_log(user_id, target_date)  # 두 번째 호출 — 캐시 히트

        # then
        assert result == expected_value
        assert call_count.call_count == 1

    def test_cacheable_TTL이_적용된다(self, fake_redis: Redis):
        # given
        user_id = 1
        target_date = "2025-01-01"
        expected_ttl = CacheTTL.SECONDS_30

        @cacheable(key=CacheKey.WORK_LOG_PLATFORM, ttl=expected_ttl)
        def get_work_log(user_id: int, target_date: str) -> dict:
            return {"data": "value"}

        expected_key = resolve_cache_key(
            CacheKey.WORK_LOG_PLATFORM, get_work_log, user_id, target_date
        )

        # when
        get_work_log(user_id, target_date)

        # then
        ttl = int(fake_redis.ttl(expected_key))  # pyright: ignore [reportArgumentType]
        assert 0 < ttl <= expected_ttl


class CachePutTest:

    def test_cache_put_함수를_실행하고_결과를_캐시에_저장한다(self, fake_redis: Redis):
        # given
        user_id = 1
        target_date = "2025-01-01"
        expected_value = {"updated": True}
        mock_fn = MagicMock(return_value=expected_value)

        @cache_put(key=CacheKey.WORK_LOG_PLATFORM, ttl=CacheTTL.DEFAULT)
        def update_work_log(user_id: int, target_date: str) -> dict:
            return mock_fn(user_id, target_date)

        expected_key = resolve_cache_key(
            CacheKey.WORK_LOG_PLATFORM, update_work_log, user_id, target_date
        )

        # when
        result = update_work_log(user_id, target_date)

        # then
        assert result == expected_value
        mock_fn.assert_called_once_with(user_id, target_date)
        assert fake_redis.exists(expected_key)

    def test_cache_put_기존_캐시를_덮어쓴다(self, fake_redis: Redis):
        # given
        user_id = 1
        target_date = "2025-01-01"
        call_count = 0

        @cache_put(key=CacheKey.WORK_LOG_PLATFORM, ttl=CacheTTL.DEFAULT)
        def update_work_log(user_id: int, target_date: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"version": call_count}

        expected_key = resolve_cache_key(
            CacheKey.WORK_LOG_PLATFORM, update_work_log, user_id, target_date
        )
        expected_value = {"version": 2}

        update_work_log(user_id, target_date)  # 첫 호출 — version 1 캐시

        # when
        result = update_work_log(user_id, target_date)  # 두 번째 호출 — version 2로 덮어쓰기

        # then
        assert result == expected_value
        cached = CacheService(fake_redis).get(expected_key)
        assert cached == expected_value


class CacheEvictTest:

    def test_cache_evict_함수를_실행하고_캐시를_삭제한다(self, fake_redis: Redis):
        # given
        user_id = 1
        target_date = "2025-01-01"
        mock_fn = MagicMock(return_value=None)

        @cache_evict(key=CacheKey.WORK_LOG_PLATFORM)
        def delete_work_log(user_id: int, target_date: str) -> None:
            return mock_fn(user_id, target_date)

        expected_key = resolve_cache_key(
            CacheKey.WORK_LOG_PLATFORM, delete_work_log, user_id, target_date
        )

        cache_service = CacheService(fake_redis)
        cache_service.set(expected_key, {"data": "old"})

        # when
        result = delete_work_log(user_id, target_date)

        # then
        assert result is None
        mock_fn.assert_called_once_with(user_id, target_date)
        assert not fake_redis.exists(expected_key)
