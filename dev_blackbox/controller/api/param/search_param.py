from pydantic import BaseModel, Field


class SearchParam(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
    similarity: float = Field(0.5, ge=0.0, le=1.0)
