from datetime import datetime

from pydantic import BaseModel


class CreateJiraSecretRequestDto(BaseModel):
    name: str
    url: str
    username: str
    api_token: str


class JiraSecretResponseDto(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime
    updated_at: datetime


class SyncJiraUsersRequestDto(BaseModel):
    project: str
