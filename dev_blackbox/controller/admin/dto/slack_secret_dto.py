from datetime import datetime

from pydantic import BaseModel


class CreateSlackSecretRequestDto(BaseModel):
    name: str
    bot_token: str


class SlackSecretResponseDto(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
