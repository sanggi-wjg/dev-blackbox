from pydantic import BaseModel


class CreateJiraSecretCommand(BaseModel):
    name: str
    url: str
    username: str
    api_token: str
