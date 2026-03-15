from pydantic import BaseModel


class SearchQuery(BaseModel):
    user_id: int
    query_text: str
    limit: int = 10
