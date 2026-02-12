from typing import Any

from llama_index.core.llms import LLM
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "gemini-3-flash-preview:cloud"
    temperature: float = 0.6
    top_k: int = 30
    top_p: float = 0.85
    request_timeout: float = 240.0
    keep_alive: float = 300.0
    context_window: int = 8000
    extra: dict[str, Any] = Field(
        default_factory=lambda: {
            "repeat_penalty": 1.2,
            "num_predict": 1024,
        }
    )

    def create_llm(self) -> LLM:
        return Ollama(
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            top_k=self.top_k,
            top_p=self.top_p,
            request_timeout=self.request_timeout,
            keep_alive=self.keep_alive,
            context_window=self.context_window,
            additional_kwargs=self.extra,
        )


class SummaryOllamaConfig(OllamaConfig):
    temperature: float = 0.1
    context_window: int = 64000
    extra: dict[str, Any] = {
        "repeat_penalty": 1.2,
        "num_predict": 4096,
    }
