from pydantic import BaseModel, Field


class JiraUserParam(BaseModel):
    jira_secret_id: int | None = Field(default=None, description="Jira 시크릿 ID")
