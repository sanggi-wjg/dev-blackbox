from pydantic import BaseModel


class SaveImageCommand(BaseModel):
    user_id: int
    filename: str
    content_type: str
    file_size: int
    data: bytes
