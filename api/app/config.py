from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "prod"
    llm_provider: Literal["openai", "mock"] = "mock"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-6-luna"
    openai_base_url: str | None = None
    llm_max_tokens: int = 4000
    llm_timeout_s: float = 25
    llm_temperature: float | None = None
    llm_reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = None
    allowed_origins: str = "https://pwnaxe.github.io"
    max_file_mb: int = 10
    max_pages: int = 100
    max_text_chars: int = 400_000
    chunk_chars: int = 12_000
    max_chunks: int = 12
    direct_summary_chars: int = 150_000
    rate_limit_per_10min: int = 15
    trust_proxy: bool = False

    @model_validator(mode="after")
    def _require_key_for_openai(self) -> "Settings":
        if self.llm_provider == "openai" and not (
            self.openai_api_key and self.openai_api_key.get_secret_value()
        ):
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return self

    @property
    def origins(self) -> list[str]:
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if self.env == "dev":
            origins.append("http://localhost:5173")
        return origins

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
