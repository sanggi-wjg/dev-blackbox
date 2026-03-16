from datetime import date

from pydantic import BaseModel

from dev_blackbox.core.enum import PlatformEnum


class SearchQuery(BaseModel):
    user_id: int
    query_text: str
    limit: int = 10
    similarity: float = 0.5
    platform: PlatformEnum | None = None
    from_date: date | None = None
    to_date: date | None = None
