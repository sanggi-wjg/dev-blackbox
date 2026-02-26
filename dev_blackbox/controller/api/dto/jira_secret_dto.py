from pydantic import BaseModel


class JiraSecretSimpleResponseDto(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    url: str
