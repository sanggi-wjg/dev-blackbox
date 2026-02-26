from datetime import date

from pydantic import BaseModel


class SlackMessageResponseDto(BaseModel):
    id: int
    target_date: date
    channel_id: str
    channel_name: str
    message_ts: str
    message_text: str
    thread_ts: str | None

    model_config = {"from_attributes": True}
