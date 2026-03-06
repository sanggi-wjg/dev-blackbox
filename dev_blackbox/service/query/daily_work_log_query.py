from datetime import date

from pydantic import BaseModel


class DailyWorkLogQuery(BaseModel):
    user_id: int
    target_date: date
