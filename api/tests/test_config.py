import pytest
from pydantic import ValidationError

from app.config import Settings


def make(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_defaults() -> None:
    settings = make()
    assert settings.llm_provider == "mock"
    assert settings.openai_model == "gpt-6-luna"
    assert settings.origins == ["https://pwnaxe.github.io"]
    assert settings.max_file_bytes == 10 * 1024 * 1024


def test_openai_requires_key() -> None:
    with pytest.raises(ValidationError):
        make(llm_provider="openai")
    with pytest.raises(ValidationError):
        make(llm_provider="openai", openai_api_key="")


def test_openai_with_key() -> None:
    assert make(llm_provider="openai", openai_api_key="placeholder").llm_provider == "openai"


def test_origins_list_and_dev() -> None:
    settings = make(allowed_origins="https://a.example, https://b.example", env="dev")
    assert settings.origins == ["https://a.example", "https://b.example", "http://localhost:5173"]


def test_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_PAGES", "7")
    monkeypatch.setenv("TRUST_PROXY", "true")
    settings = make()
    assert settings.max_pages == 7
    assert settings.trust_proxy is True


def test_llm_options_unset_by_default() -> None:
    settings = make()
    assert settings.llm_temperature is None
    assert settings.llm_reasoning_effort is None


def test_llm_options_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    settings = make()
    assert settings.llm_temperature == 0.2
    assert settings.llm_reasoning_effort == "low"


def test_invalid_reasoning_effort() -> None:
    with pytest.raises(ValidationError):
        make(llm_reasoning_effort="extreme")


@pytest.mark.parametrize("effort", ["none", "minimal", "low", "medium", "high", "xhigh"])
def test_reasoning_effort_values(effort: str) -> None:
    assert make(llm_reasoning_effort=effort).llm_reasoning_effort == effort


def test_chunk_chars_default() -> None:
    assert make().chunk_chars == 12_000
