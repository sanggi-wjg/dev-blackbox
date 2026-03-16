from datetime import date

from pydantic import BaseModel

from dev_blackbox.core.enum import PlatformEnum


class SavePlatformWorkLogCommand(BaseModel):
    user_id: int
    target_date: date
    platform: PlatformEnum
    content: str
    model_name: str
    prompt: str
    is_empty: bool
