from functools import lru_cache

from httpx import TimeoutException
from llama_index.embeddings.ollama import OllamaEmbedding
from tenacity import retry, stop_after_attempt, retry_if_exception_type

from dev_blackbox.agent.model.llm_model import EmbeddingOllamaConfig


class EmbeddingAgent:

    def __init__(self, embedding: OllamaEmbedding):
        self.embedding = embedding

    @classmethod
    def create_with_ollama(cls, config: EmbeddingOllamaConfig) -> "EmbeddingAgent":
        return cls(
            embedding=OllamaEmbedding(
                base_url=config.base_url,
                model_name=config.model,
                request_timeout=config.request_timeout,
            ),
        )

    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((TimeoutException,)),
    )
    def get_embedding(self, text: str) -> list[float]:
        return self.embedding.get_text_embedding(text)


@lru_cache(maxsize=10)
def get_embedding_agent(
    config: EmbeddingOllamaConfig = EmbeddingOllamaConfig(),
) -> EmbeddingAgent:
    return EmbeddingAgent.create_with_ollama(config)
