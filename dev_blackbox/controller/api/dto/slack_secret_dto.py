from pydantic import BaseModel


class SlackSecretSimpleResponseDto(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
