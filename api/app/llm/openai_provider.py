import logging

import openai
from openai import AsyncOpenAI

from app.config import Settings
from app.llm.base import LLMError, LLMTimeout

logger = logging.getLogger(__name__)


def describe_api_error(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    message = getattr(exc, "message", None) or str(exc)
    prefix = f"{status} " if status is not None else ""
    return f"{prefix}{message}"[:300]


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        assert settings.openai_api_key is not None
        self._model = settings.openai_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature
        self._reasoning_effort = settings.llm_reasoning_effort
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_s,
            max_retries=0,
        )

    def optional_params(self) -> dict:
        # some models only accept the default temperature, so send it only when configured
        options: dict = {}
        if self._temperature is not None:
            options["temperature"] = self._temperature
        if self._reasoning_effort is not None:
            options["reasoning_effort"] = self._reasoning_effort
        return options

    async def complete_json(
        self, system: str, user: str, schema_name: str, json_schema: dict
    ) -> str:
        options = self.optional_params()
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": schema_name, "schema": json_schema, "strict": True},
                },
                max_completion_tokens=self._max_tokens,
                **options,
            )
        except openai.APITimeoutError as exc:
            raise LLMTimeout from exc
        except openai.OpenAIError as exc:
            logger.warning("LLMError %s: %s", type(exc).__name__, describe_api_error(exc))
            raise LLMError(type(exc).__name__) from exc
        content = response.choices[0].message.content
        if not content:
            logger.warning("LLMError: empty completion")
            raise LLMError("empty completion")
        return content
