import json
import logging
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.llm import build_provider
from app.llm.base import LLMError
from app.llm.mock import MockProvider
from app.llm.openai_provider import OpenAIProvider
from app.pdf import PageText
from app.prompts import document_user_prompt, final_user_prompt, system_prompt
from app.schemas import ChunkOutput, FinalOutput, ModelOutput

pytestmark = pytest.mark.anyio


def walk_objects(node: object):
    if isinstance(node, dict):
        if node.get("type") == "object":
            yield node
        for value in node.values():
            yield from walk_objects(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_objects(value)


@pytest.mark.parametrize("model", [ModelOutput, ChunkOutput, FinalOutput])
def test_wire_schemas_are_strict_compatible(model: type) -> None:
    schema = model.model_json_schema()
    assert "keyPoints" in schema["properties"]
    for obj in walk_objects(schema):
        assert obj["additionalProperties"] is False
        assert sorted(obj["required"]) == sorted(obj["properties"])


def test_factory_returns_mock_by_default() -> None:
    assert isinstance(build_provider(Settings()), MockProvider)


async def test_mock_extracts_facts() -> None:
    text = (
        "UMOWA NR 1/2026\nzawarta 12.03.2026 r. pomiędzy Alfa Beta sp. z o.o. a Gamma S.A.\n"
        "Wynagrodzenie 184 500,00 zł oraz 8 600 EUR i 890 USD. Termin: 5 maja 2026."
    )
    user = document_user_prompt([PageText(1, text)])
    raw = await MockProvider().complete_json("", user, "analysis", {})
    out = ModelOutput.model_validate(json.loads(raw))
    assert out.type == "umowa"
    assert out.language == "pl"
    assert out.date == "2026-03-12"
    assert [(a.value, a.currency) for a in out.amounts] == [
        (184500.0, "PLN"),
        (8600.0, "EUR"),
        (890.0, "USD"),
    ]
    assert [d.date for d in out.dates] == ["2026-03-12", "2026-05-05"]
    assert out.entities.organizations == ["Alfa Beta sp. z o.o.", "Gamma S.A."]
    assert out.injection_detected is False


async def test_mock_final_output_is_valid() -> None:
    user = final_user_prompt(["Zdanie jeden. Zdanie dwa."], ["punkt 1", "punkt 2"])
    raw = await MockProvider().complete_json("", user, "final", {})
    FinalOutput.model_validate(json.loads(raw))


def openai_settings(**kwargs: object) -> Settings:
    return Settings(llm_provider="openai", openai_api_key="placeholder", **kwargs)


def test_optional_params_omitted_by_default() -> None:
    assert OpenAIProvider(openai_settings()).optional_params() == {}


def test_optional_params_when_set() -> None:
    provider = OpenAIProvider(openai_settings(llm_temperature=0.1, llm_reasoning_effort="low"))
    assert provider.optional_params() == {"temperature": 0.1, "reasoning_effort": "low"}


class FailingCompletions:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc
        self.kwargs: dict = {}

    async def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        raise self.exc


async def test_request_kwargs_and_error_logging(caplog: pytest.LogCaptureFixture) -> None:
    import httpx
    import openai

    request = httpx.Request("POST", "https://api.example/v1/chat/completions")
    response = httpx.Response(400, request=request)
    error = openai.BadRequestError("Unsupported value: temperature", response=response, body=None)
    completions = FailingCompletions(error)
    provider = OpenAIProvider(openai_settings(llm_reasoning_effort="low"))
    provider._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    with caplog.at_level(logging.WARNING), pytest.raises(LLMError):
        await provider.complete_json("sys", "secret document text", "analysis", {})
    assert completions.kwargs["reasoning_effort"] == "low"
    assert "temperature" not in completions.kwargs
    assert len(caplog.records) == 1
    line = caplog.records[0].getMessage()
    assert "BadRequestError" in line
    assert "400" in line
    assert "Unsupported value: temperature" in line
    assert "secret document text" not in line


async def test_mock_summary_output_is_valid() -> None:
    user = document_user_prompt([PageText(1, "Umowa z Firma sp. z o.o. na kwotę 100 zł.")])
    raw = await MockProvider().complete_json("", user, "summary", {})
    out = FinalOutput.model_validate_json(raw)
    assert 3 <= len(out.key_points) <= 7


def mock_user(text: str) -> str:
    return document_user_prompt([PageText(1, text)])


@pytest.mark.parametrize(
    ("text", "marker"),
    [
        ("UMOWA NR 1/2026 zawarta między Alfa sp. z o.o. oraz Beta S.A. w Łodzi", "Dokument typu"),
        (
            "AGREEMENT NO. 1/2026 made between the Seller and the Buyer for the supply of goods",
            "classified as",
        ),
    ],
)
async def test_mock_answers_in_the_document_language(text: str, marker: str) -> None:
    raw = await MockProvider().complete_json(
        system_prompt("analysis"), mock_user(text), "analysis", {}
    )
    assert marker in ModelOutput.model_validate(json.loads(raw)).summary


async def test_mock_dates_keep_their_precision() -> None:
    text = (
        "UMOWA NR 1/2026\nZawarta 12 marca 2026 r. Wdrożenie w marcu 2027 nie jest datą.\n"
        "Przegląd: czerwiec 2027. Budżet na rok w roku 2028. Płatność 05.05.2026."
    )
    raw = await MockProvider().complete_json("", mock_user(text), "analysis", {})
    out = ModelOutput.model_validate(json.loads(raw))
    assert {(d.date, d.precision) for d in out.dates} == {
        ("2026-03-12", "day"),
        ("2027-06", "month"),
        ("2028", "year"),
        ("2026-05-05", "day"),
    }
    assert out.date == "2026-03-12"


async def test_mock_document_date_is_null_without_a_full_day() -> None:
    raw = await MockProvider().complete_json("", mock_user("UMOWA\nStyczeń 2026."), "analysis", {})
    out = ModelOutput.model_validate(json.loads(raw))
    assert out.date is None
    assert [(d.date, d.precision) for d in out.dates] == [("2026-01", "month")]


async def test_mock_subtype_for_a_cv_and_none_for_a_contract() -> None:
    cv = await MockProvider().complete_json(
        "", mock_user("Jan Kowalski\nCV\nDoświadczenie"), "analysis", {}
    )
    out = ModelOutput.model_validate(json.loads(cv))
    assert (out.type, out.subtype) == ("inne", "cv")
    contract = await MockProvider().complete_json("", mock_user("UMOWA NR 1/2026"), "analysis", {})
    assert ModelOutput.model_validate(json.loads(contract)).subtype is None
