from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.user import User


class AuthenticatedUser(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    tz_info: ZoneInfo
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: User) -> AuthenticatedUser:
        return cls(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            timezone=entity.timezone,
            tz_info=entity.tz_info,
            is_admin=entity.is_admin,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
