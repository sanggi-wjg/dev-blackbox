from datetime import date

from pydantic import BaseModel


class SaveGitHubEventsCommand(BaseModel):
    user_id: int
    target_date: date | None = None
