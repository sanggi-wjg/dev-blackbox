from pydantic import BaseModel


class SlackUserQuery(BaseModel):
    slack_secret_id: int | None = None
