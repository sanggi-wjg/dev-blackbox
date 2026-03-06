from datetime import date

from pydantic import BaseModel


class PlatformWorkLogQuery(BaseModel):
    user_id: int
    target_date: date
