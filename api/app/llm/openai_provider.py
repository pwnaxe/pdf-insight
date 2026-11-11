import openai
from openai import AsyncOpenAI

from app.config import Settings
from app.llm.base import LLMError, LLMTimeout


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        assert settings.openai_api_key is not None
        self._model = settings.openai_model
        self._max_tokens = settings.llm_max_tokens
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_s,
            max_retries=0,
        )

    async def complete_json(
        self, system: str, user: str, schema_name: str, json_schema: dict
    ) -> str:
        options: dict = {}
        # reasoning models reject a custom temperature
        if not self._model.startswith(("gpt-5", "o")):
            options["temperature"] = 0.1
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
            raise LLMError(type(exc).__name__) from exc
        content = response.choices[0].message.content
        if not content:
            raise LLMError("empty completion")
        return content
