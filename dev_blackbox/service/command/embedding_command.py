from pydantic import BaseModel


class GeneratePlatformWorkLogEmbeddingCommand(BaseModel):
    platform_work_log_id: int
    chunk_index: int
    chunk_text: str
    embedding: list[float]
