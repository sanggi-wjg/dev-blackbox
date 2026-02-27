from datetime import datetime

from pydantic import BaseModel


class SlackUserResponseDto(BaseModel):
    id: int
    slack_secret_id: int
    member_id: str
    is_active: bool
    display_name: str
    real_name: str
    email: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime


class AssignSlackUserRequestDto(BaseModel):
    slack_secret_id: int
    slack_user_id: int
