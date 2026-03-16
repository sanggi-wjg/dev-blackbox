from typing import NamedTuple

from dev_blackbox.storage.rds.entity import PlatformWorkLog


class ChunkSearchResult(NamedTuple):
    chunk_index: int
    chunk_text: str
    distance: float


class PlatformWorkLogSearchResult(NamedTuple):
    platform_work_log: PlatformWorkLog
    distance: float
    chunk_results: list[ChunkSearchResult]
    chunk_count: int
