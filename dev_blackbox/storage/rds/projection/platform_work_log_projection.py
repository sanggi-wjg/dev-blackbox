from typing import NamedTuple

from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog


class PlatformWorkLogWithDistanceProjection(NamedTuple):
    platform_work_log: PlatformWorkLog
    distance: float
