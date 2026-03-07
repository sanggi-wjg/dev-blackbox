from datetime import date

from pydantic import BaseModel


class SaveDailyWorkLogCommand(BaseModel):
    user_id: int
    target_date: date
