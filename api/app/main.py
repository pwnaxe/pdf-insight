import logging
import math
import time
import tomllib
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
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
from app.security_headers import SecurityHeadersMiddleware, apply_security_headers

logger = logging.getLogger("pdf_insight")

READ_CHUNK = 1024 * 1024
RATE_WINDOW_S = 600
REPO_URL = "https://github.com/pwnaxe/pdf-insight"
API_NAME = "pdf-insight-api"


def _app_version() -> str:
    # the Docker image installs dependencies only, not the project, so metadata is unavailable
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"


def _http_error_code(status: int) -> str:
    if status == 404:
        return "NOT_FOUND"
    if status == 405:
        return "METHOD_NOT_ALLOWED"
    return "VALIDATION_ERROR" if status < 500 else "INTERNAL_ERROR"


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
    # the interactive docs expose the schema, so they are dev-only
    docs = (
        {} if settings.env == "dev" else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    )
    app = FastAPI(title="PDF Insight API", version=_app_version(), **docs)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["POST", "GET"],
        # the client sends a multipart POST with no custom headers; CORS-safelisted ones always pass
        allow_headers=[],
        allow_credentials=False,
    )
    app.add_middleware(SecurityHeadersMiddleware)

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error_response(exc.status, exc.code, exc.message, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        # the form is not parsed when validation fails, so the language is unknown here
        return _error_response(422, "VALIDATION_ERROR", error_message("VALIDATION_ERROR", "en"))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _http_error_code(exc.status_code)
        headers = (
            {"Allow": exc.headers["Allow"]} if exc.headers and "Allow" in exc.headers else None
        )
        return _error_response(exc.status_code, code, error_message(code, "en"), headers)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled error: %s", type(exc).__name__)
        response = _error_response(500, "INTERNAL_ERROR", error_message("INTERNAL_ERROR", "en"))
        # this response is built outside the user middleware stack, so add the headers here
        apply_security_headers(response.headers, request.url.path)
        return response

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, object]:
        endpoints = sorted(
            f"{method} {route.path}"
            for route in app.routes
            if isinstance(route, APIRoute) and route.path != "/"
            for method in route.methods - {"HEAD", "OPTIONS"}
        )
        return {
            "name": API_NAME,
            "version": _app_version(),
            "endpoints": endpoints,
            "repo": REPO_URL,
        }

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
                raise ApiError(
                    "UNSUPPORTED_MEDIA_TYPE", error_message("UNSUPPORTED_MEDIA_TYPE", language), 415
                )

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
