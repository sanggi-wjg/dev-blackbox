from unittest.mock import patch, MagicMock

from redis import Redis

from dev_blackbox.util.distributed_lock import distributed_lock


class DistributedLockTest:

    def test_락을_획득하면_True를_반환한다(self, fake_redis: Redis):
        # given
        lock_key = "test:lock:acquire"

        # when
        with distributed_lock(lock_key, timeout=10) as acquired:
            # then
            assert acquired is True

    def test_락_획득_후_블록_내부가_실행된다(self, fake_redis: Redis):
        # given
        lock_key = "test:lock:execution"
        executed = False

        # when
        with distributed_lock(lock_key, timeout=10) as acquired:
            if acquired:
                executed = True

        # then
        assert executed is True

    def test_이미_획득된_락은_False를_반환한다(self, fake_redis: Redis):
        # given
        lock_key = "test:lock:already-held"

        # when
        with distributed_lock(lock_key, timeout=10) as first:
            assert first is True

            with distributed_lock(lock_key, timeout=10) as second:
                # then
                assert second is False

    def test_락_해제_후_재획득이_가능하다(self):
        # given
        lock_key = "test:lock:reacquire"
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when — 첫 번째 획득 후 해제
            with distributed_lock(lock_key, timeout=10) as first:
                assert first is True

            # then — 해제 후 재획득 가능
            with distributed_lock(lock_key, timeout=10) as second:
                assert second is True

            assert mock_lock.release.call_count == 2

    def test_락_획득_중_예외가_발생하면_False를_반환한다(self):
        # given
        lock_key = "test:lock:acquire-error"
        mock_lock = MagicMock()
        mock_lock.acquire.side_effect = Exception("Redis connection error")

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when
            with distributed_lock(lock_key, timeout=10) as acquired:
                # then
                assert acquired is False

    def test_락_해제_중_예외가_발생해도_전파되지_않는다(self):
        # given
        lock_key = "test:lock:release-error"
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True
        mock_lock.release.side_effect = Exception("Lock already expired")

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when / then — 예외가 전파되지 않아야 한다
            with distributed_lock(lock_key, timeout=10) as acquired:
                assert acquired is True

    def test_블록_내부_예외가_발생해도_락이_해제된다(self):
        # given
        lock_key = "test:lock:block-error"
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when
            try:
                with distributed_lock(lock_key, timeout=10) as acquired:
                    assert acquired is True
                    raise ValueError("작업 중 에러 발생")
            except ValueError:
                pass

            # then
            mock_lock.release.assert_called_once()

    def test_락_미획득_시_해제를_호출하지_않는다(self):
        # given
        lock_key = "test:lock:no-release"
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = False

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when
            with distributed_lock(lock_key, timeout=10) as acquired:
                assert acquired is False

            # then
            mock_lock.release.assert_not_called()

    def test_blocking_timeout이_양수이면_blocking_모드로_acquire한다(self):
        # given
        lock_key = "test:lock:blocking"
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when
            with distributed_lock(lock_key, timeout=10, blocking_timeout=5) as acquired:
                assert acquired is True

            # then — blocking=True로 호출되어야 한다
            mock_lock.acquire.assert_called_once_with(blocking=True)

    def test_blocking_timeout이_0이면_non_blocking_모드로_acquire한다(self):
        # given
        lock_key = "test:lock:non-blocking"
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        with patch("dev_blackbox.util.distributed_lock.LockService") as mock_lock_service:
            mock_lock_service.return_value.lock.return_value = mock_lock

            # when
            with distributed_lock(lock_key, timeout=10, blocking_timeout=0) as acquired:
                assert acquired is True

            # then — blocking=False로 호출되어야 한다
            mock_lock.acquire.assert_called_once_with(blocking=False)