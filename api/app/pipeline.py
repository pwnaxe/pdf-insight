import asyncio
import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.chunking import chunk_pages
from app.config import Settings
from app.errors import ApiError
from app.injection import find_injections
from app.llm import LLMError, LLMProvider, LLMTimeout
from app.merge import merge_chunk_outputs
from app.pdf import ExtractedPdf, PageText
from app.prompts import document_user_prompt, final_user_prompt, retry_user_prompt, system_prompt
from app.schemas import (
    AnalysisResult,
    ChunkOutput,
    DocumentInfo,
    Entities,
    FinalOutput,
    ModelOutput,
)

CHUNK_CONCURRENCY = 3

_UNSAFE_NAME = re.compile(r"[\x00-\x1f\x7f<>:\"|?*]")


@dataclass(frozen=True)
class AnalysisRun:
    result: AnalysisResult
    chunks: int


def sanitize_file_name(raw: str | None) -> str:
    name = (raw or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = _UNSAFE_NAME.sub("", name).strip(" .")[:200]
    return name or "dokument.pdf"


async def _call[T: BaseModel](
    provider: LLMProvider, schema_name: str, model: type[T], user: str
) -> T:
    system = system_prompt(schema_name)
    schema = model.model_json_schema()
    prompt = user
    for attempt in range(2):
        try:
            raw = await provider.complete_json(system, prompt, schema_name, schema)
        except (LLMTimeout, TimeoutError) as exc:
            raise ApiError(
                "AI_TIMEOUT", "Model AI nie odpowiedział w wymaganym czasie. Spróbuj ponownie.", 504
            ) from exc
        except LLMError as exc:
            raise ApiError(
                "AI_ERROR", "Usługa AI jest chwilowo niedostępna. Spróbuj ponownie później.", 502
            ) from exc
        try:
            return model.model_validate(json.loads(raw))
        except (ValueError, ValidationError) as exc:
            if attempt == 1:
                raise ApiError(
                    "AI_INVALID_OUTPUT", "Model AI zwrócił niepoprawną odpowiedź.", 502
                ) from exc
            prompt = retry_user_prompt(user, str(exc))
    raise AssertionError("unreachable")


async def _extract_chunks(provider: LLMProvider, chunks: list[list[PageText]]) -> list[ChunkOutput]:
    semaphore = asyncio.Semaphore(CHUNK_CONCURRENCY)

    async def run(pages: list[PageText]) -> ChunkOutput:
        async with semaphore:
            return await _call(provider, "chunk", ChunkOutput, document_user_prompt(pages))

    return list(await asyncio.gather(*(run(pages) for pages in chunks)))


def _page_list(pages: list[int]) -> str:
    return ", ".join(str(p) for p in pages)


def _warnings(
    extracted: ExtractedPdf, truncated: bool, injection_pages: list[int], model_flag: bool
) -> list[str]:
    warnings: list[str] = []
    if injection_pages:
        label = "strona" if len(injection_pages) == 1 else "strony"
        warnings.append(
            "Dokument zawiera tekst, który próbuje wydawać polecenia systemowi AI "
            f"({label} {_page_list(injection_pages)}). Zignorowano go podczas analizy."
        )
    elif model_flag:
        warnings.append(
            "Dokument zawiera tekst, który próbuje wydawać polecenia systemowi AI. "
            "Zignorowano go podczas analizy."
        )
    if extracted.pages_without_text:
        warnings.append(
            f"Strony bez warstwy tekstowej (pominięte): {_page_list(extracted.pages_without_text)}."
        )
    if truncated:
        warnings.append(
            "Dokument jest bardzo długi, więc przeanalizowano tylko jego początkową część."
        )
    return warnings


async def analyze_document(
    extracted: ExtractedPdf, file_name: str, provider: LLMProvider, settings: Settings
) -> AnalysisRun:
    plan = chunk_pages(extracted.pages, settings.chunk_chars, settings.max_chunks)

    if len(plan.chunks) == 1:
        out = await _call(provider, "analysis", ModelOutput, document_user_prompt(plan.chunks[0]))
        fields = out.model_dump()
        fields.pop("injection_detected")
        fields.pop("injection_quotes")
        model_flag = out.injection_detected
    else:
        outputs = await _extract_chunks(provider, plan.chunks)
        merged = merge_chunk_outputs(outputs)
        final = await _call(
            provider,
            "final",
            FinalOutput,
            final_user_prompt(merged.summaries, merged.key_points),
        )
        fields = {
            "language": merged.language,
            "type": merged.type,
            "title": merged.title,
            "date": merged.date,
            "summary": final.summary,
            "key_points": final.key_points,
            "entities": Entities(organizations=merged.organizations, people=merged.people),
            "amounts": merged.amounts,
            "dates": merged.dates,
            "keywords": merged.keywords,
        }
        model_flag = merged.injection_detected

    hits = find_injections(extracted.pages)
    injection_pages = sorted({hit.page for hit in hits})
    warnings = _warnings(
        extracted, extracted.truncated or plan.truncated, injection_pages, model_flag
    )

    try:
        result = AnalysisResult(
            document=DocumentInfo(
                file_name=sanitize_file_name(file_name),
                pages=extracted.page_count,
                language=fields["language"],
                type=fields["type"],
                title=fields["title"],
                date=fields["date"],
            ),
            summary=fields["summary"],
            key_points=fields["key_points"],
            entities=fields["entities"],
            amounts=fields["amounts"],
            dates=fields["dates"],
            keywords=fields["keywords"],
            suspected_injection=bool(hits) or model_flag,
            warnings=warnings,
        )
    except ValidationError as exc:
        raise ApiError("AI_INVALID_OUTPUT", "Model AI zwrócił niepoprawną odpowiedź.", 502) from exc
    return AnalysisRun(result, len(plan.chunks))
