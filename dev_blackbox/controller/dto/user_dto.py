from datetime import datetime

from pydantic import BaseModel, EmailStr

from dev_blackbox.core.types import NotBlankStr


class CreateUserRequestDto(BaseModel):
    name: NotBlankStr
    email: EmailStr


class UserResponseDto(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
