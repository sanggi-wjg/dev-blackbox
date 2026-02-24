from datetime import datetime

from pydantic import BaseModel


class JiraUserResponseDto(BaseModel):
    id: int
    account_id: str
    active: bool
    display_name: str
    email_address: str
    url: str
    project: str | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime


class AssignJiraUserRequestDto(BaseModel):
    project: str
