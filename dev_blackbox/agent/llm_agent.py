from httpx import TimeoutException
from llama_index.core.llms import LLM
from llama_index.core.prompts import PromptTemplate
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from dev_blackbox.agent.model.llm_model import OllamaConfig


class LLMAgent:
    """
    TODO
     프롬프트 템플릿과 LLM 모델, 파라미터를 RDS에 저장하거나 요청을 받아서 커스텀하게 사용하도록 개선
    """

    def __init__(self, llm: LLM):
        self.llm = llm

    @classmethod
    def create_with_ollama(
        cls,
        config: OllamaConfig = OllamaConfig(),
    ) -> LLMAgent:
        return LLMAgent(
            llm=config.create_llm(),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=10, max=60),
        retry=retry_if_exception_type((TimeoutException,)),
    )
    def query(self, prompt: PromptTemplate, **kwargs) -> str:
        formatted = prompt.format(**kwargs)
        response = self.llm.complete(formatted)
        return response.text.strip()
