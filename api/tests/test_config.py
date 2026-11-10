import pytest
from pydantic import ValidationError

from app.config import Settings


def make(**kwargs: object) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_defaults() -> None:
    settings = make()
    assert settings.llm_provider == "mock"
    assert settings.openai_model == "gpt-4.1-mini"
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
