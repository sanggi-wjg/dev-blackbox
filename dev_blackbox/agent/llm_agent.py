from llama_index.core.llms import LLM
from llama_index.core.prompts import PromptTemplate

from dev_blackbox.agent.model.llm_model import OllamaConfig


class LLMAgent:

    def __init__(self, llm: LLM):
        self._llm = llm

    @classmethod
    def create_with_ollama(
        cls,
        config: OllamaConfig = OllamaConfig(),
    ) -> LLMAgent:
        return LLMAgent(
            llm=config.create_llm(),
        )

    def query(self, prompt: PromptTemplate, **kwargs) -> str:
        formatted = prompt.format(**kwargs)
        response = self._llm.complete(formatted)
        return response.text.strip()
