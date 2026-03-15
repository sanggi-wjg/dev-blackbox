from datetime import date
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity import PlatformWorkLogChunk


class EventCountByDateProjection(NamedTuple):
    target_date: date
    event_count: int


class PlatformWorkLogChunkWithDistanceProjection(NamedTuple):
    platform_work_log_chunk: PlatformWorkLogChunk
    distance: float
