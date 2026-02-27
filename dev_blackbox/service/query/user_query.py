from pydantic import BaseModel


class UserQuery(BaseModel):
    name: str | None = None
    is_deleted: bool | None = None
