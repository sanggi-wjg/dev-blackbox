from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
    from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog


class EmbeddingContext(BaseModel):
    work_log_id: int
    content: str

    @classmethod
    def from_platform_work_log(cls, entity: PlatformWorkLog) -> EmbeddingContext:
        return cls(work_log_id=entity.id, content=entity.content)

    @classmethod
    def from_daily_work_log(cls, entity: DailyWorkLog) -> EmbeddingContext:
        return cls(work_log_id=entity.id, content=entity.content)
