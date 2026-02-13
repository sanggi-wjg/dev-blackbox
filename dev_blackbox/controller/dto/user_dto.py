from datetime import datetime

from pydantic import BaseModel, EmailStr


class CreateUserRequestDto(BaseModel):
    name: str
    email: EmailStr


class UserResponseDto(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
