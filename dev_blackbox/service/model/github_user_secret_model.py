from pydantic import BaseModel


class GitHubUserSecretModel(BaseModel):
    id: int
    username: str
    personal_access_token: str

    model_config = {"from_attributes": True}
