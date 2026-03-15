from pydantic import BaseModel


class UpdatePlatformWorkLogEmbeddingCommand(BaseModel):
    work_log_id: int
    embedding: list[float]
