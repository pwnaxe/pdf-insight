from app.config import Settings
from app.llm.base import LLMError, LLMProvider, LLMTimeout
from app.llm.mock import MockProvider
from app.llm.openai_provider import OpenAIProvider

__all__ = ["LLMError", "LLMProvider", "LLMTimeout", "build_provider"]


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings)
    return MockProvider()
