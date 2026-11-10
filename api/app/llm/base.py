from typing import Protocol


class LLMTimeout(Exception):
    pass


class LLMError(Exception):
    pass


class LLMProvider(Protocol):
    name: str

    async def complete_json(
        self, system: str, user: str, schema_name: str, json_schema: dict
    ) -> str: ...
