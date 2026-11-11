import logging
import math
import time

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Settings, get_settings
from app.errors import ApiError
from app.llm import LLMProvider, build_provider
from app.messages import DEFAULT_LANG, Lang, error_message, parse_lang
from app.pdf import extract_pdf
from app.pipeline import analyze_document
from app.ratelimit import SlidingWindowLimiter
from app.schemas import AnalysisResult

logger = logging.getLogger("pdf_insight")

READ_CHUNK = 1024 * 1024
RATE_WINDOW_S = 600


def _error_response(
    status: int, code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message}}, status_code=status, headers=headers
    )


def _client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        # the last entry is the one appended by our own proxy
        last = forwarded.split(",")[-1].strip()
        if last:
            return last
    return request.client.host if request.client else "unknown"


def _is_pdf_upload(file: UploadFile) -> bool:
    name = (file.filename or "").lower()
    return name.endswith(".pdf") or file.content_type == "application/pdf"


async def _read_capped(file: UploadFile, limit: int, message: str) -> bytes:
    data = bytearray()
    while chunk := await file.read(READ_CHUNK):
        data.extend(chunk)
        if len(data) > limit:
            raise ApiError("FILE_TOO_LARGE", message, 413)
    return bytes(data)


def create_app(settings: Settings | None = None, provider: LLMProvider | None = None) -> FastAPI:
    settings = settings or get_settings()
    provider = provider or build_provider(settings)
    limiter = SlidingWindowLimiter(settings.rate_limit_per_10min, RATE_WINDOW_S)
    app = FastAPI(title="PDF Insight API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error_response(exc.status, exc.code, exc.message, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        # the form is not parsed when validation fails, so the language is unknown here
        return _error_response(422, "VALIDATION_ERROR", error_message("VALIDATION_ERROR", "en"))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "HTTP_ERROR", error_message("HTTP_ERROR", "en"))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled error: %s", type(exc).__name__)
        return _error_response(500, "INTERNAL_ERROR", error_message("INTERNAL_ERROR", "en"))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/analyze", response_model=AnalysisResult)
    async def analyze(
        request: Request, file: UploadFile, lang: str = Form(DEFAULT_LANG)
    ) -> AnalysisResult:
        language = parse_lang(lang)
        started = time.perf_counter()
        status = 200
        pages = chunks = 0
        try:
            origin = request.headers.get("origin")
            if origin is not None and origin not in settings.origins:
                raise ApiError("FORBIDDEN_ORIGIN", error_message("FORBIDDEN_ORIGIN", language), 403)

            retry_after = limiter.check(_client_ip(request, settings))
            if retry_after is not None:
                raise ApiError(
                    "RATE_LIMITED",
                    error_message("RATE_LIMITED", language),
                    429,
                    {"Retry-After": str(math.ceil(retry_after))},
                )

            limit = settings.max_file_bytes
            declared = request.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > limit + READ_CHUNK:
                raise ApiError("FILE_TOO_LARGE", _too_large(settings, language), 413)
            data = await _read_capped(file, limit, _too_large(settings, language))

            if not data.startswith(b"%PDF-") or not _is_pdf_upload(file):
                raise ApiError("NOT_PDF", error_message("NOT_PDF", language), 415)

            extracted = await run_in_threadpool(
                extract_pdf, data, settings.max_pages, settings.max_text_chars, language
            )
            pages = extracted.page_count
            run = await analyze_document(
                extracted, file.filename or "", provider, settings, language
            )
            chunks = run.chunks
            return run.result
        except ApiError as exc:
            status = exc.status
            raise
        except Exception:
            status = 500
            raise
        finally:
            logger.info(
                "analyze status=%d duration_ms=%d pages=%d chunks=%d provider=%s",
                status,
                (time.perf_counter() - started) * 1000,
                pages,
                chunks,
                provider.name,
            )

    return app


def _too_large(settings: Settings, lang: Lang) -> str:
    return error_message("FILE_TOO_LARGE", lang, max_mb=settings.max_file_mb)


app = create_app()
