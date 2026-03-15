from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity import PlatformWorkLog, PlatformWorkLogChunk


class PlatformWorkLogSearchResult(NamedTuple):
    platform_work_log: PlatformWorkLog
    distance: float
    # chunk_results: list[PlatformWorkLogChunk]
    # chunk_count: int
