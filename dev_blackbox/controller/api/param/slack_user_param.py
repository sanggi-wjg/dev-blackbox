from pydantic import BaseModel, Field


class SlackUserParam(BaseModel):
    slack_secret_id: int | None = Field(default=None, description="Slack 시크릿 ID")
