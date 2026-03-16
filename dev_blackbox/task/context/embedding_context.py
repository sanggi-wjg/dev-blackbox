from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog


class WorkLogContentContext(BaseModel):
    platform_work_log_id: int
    content: str

    @classmethod
    def from_entity(cls, entity: PlatformWorkLog) -> WorkLogContentContext:
        return cls(
            platform_work_log_id=entity.id,
            content=entity.content,
        )


class ChunkedWorkLogContentContext(BaseModel):
    platform_work_log_id: int
    chunked_content: list[str]
