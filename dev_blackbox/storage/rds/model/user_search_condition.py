from pydantic import BaseModel


class UserSearchCondition(BaseModel):
    name: str | None = None
    is_deleted: bool | None = None
