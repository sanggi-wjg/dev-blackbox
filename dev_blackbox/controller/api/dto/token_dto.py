from pydantic import BaseModel


class TokenResponseDto(BaseModel):
    access_token: str
    token_type: str = "bearer"
