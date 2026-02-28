from pydantic import BaseModel


class CreateGitHubUserSecretCommand(BaseModel):
    user_id: int
    username: str
    personal_access_token: str
