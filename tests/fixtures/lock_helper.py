from contextlib import contextmanager


@contextmanager
def mock_lock_acquired():
    yield True


@contextmanager
def mock_lock_not_acquired():
    yield False
