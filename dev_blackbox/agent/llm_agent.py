from httpx import TimeoutException
from llama_index.core.llms import LLM
from llama_index.core.prompts import PromptTemplate
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from dev_blackbox.agent.model.llm_model import OllamaConfig


class LLMAgent:

    def __init__(self, llm: LLM):
        self._llm = llm

    @classmethod
    def create_with_ollama(
        cls,
        config: OllamaConfig = OllamaConfig(),
    ) -> LLMAgent:
        # todo rds에 설정 값 저장하여 사용 하도록
        return LLMAgent(
            llm=config.create_llm(),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=10, max=60),
        retry=retry_if_exception_type((TimeoutException,)),
    )
    def query(self, prompt: PromptTemplate, **kwargs) -> str:
        # todo rds에 프롬프트 저장하여 커스텀하게 사용 하도록
        formatted = prompt.format(**kwargs)
        response = self._llm.complete(formatted)
        return response.text.strip()
