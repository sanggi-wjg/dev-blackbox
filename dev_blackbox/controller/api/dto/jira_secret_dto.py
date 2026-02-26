from pydantic import BaseModel


class JiraSecretSimpleResponseDto(BaseModel):
    id: int
    name: str
    url: str
