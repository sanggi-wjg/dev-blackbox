from pydantic import BaseModel


class BackgroundTaskResponseDto(BaseModel):
    message: str
