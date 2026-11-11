# Security

## CORS and Origin

- `ALLOWED_ORIGINS` lists the allowed origins (default: the GitHub Pages site). With `ENV=dev`,
  `http://localhost:5173` is added.
- `CORSMiddleware` allows POST and GET, no credentials.
- `POST /api/analyze` also checks the `Origin` header itself. If it is present and not in the
  list, the API returns 403 `FORBIDDEN_ORIGIN`.
- CORS only tells browsers what a page may read. A script, `curl` or any request without an
  `Origin` header is not blocked by it. That is why the limits below exist.

## Limits

| What | Where | Default |
| --- | --- | --- |
| File size | nginx `client_max_body_size` 11m; app `MAX_FILE_MB` (read in 1 MB steps) | 10 MB |
| Pages | `MAX_PAGES`, checked before extraction | 100 |
| Text | `MAX_TEXT_CHARS`, the rest is cut and a warning is added | 400,000 chars |
| Chunks | `MAX_CHUNKS` | 12 |
| Rate, app | `RATE_LIMIT_PER_10MIN` per client IP, sliding window, in memory per process | 15 |
| Rate, nginx | `limit_req` 2 r/s per IP, burst 10, status 429 | |
| Model call timeout | `LLM_TIMEOUT_S`, no SDK retries | 25 s |
| Proxy read timeout | nginx `proxy_read_timeout` | 90 s |

The app takes the client IP from `X-Forwarded-For` only when `TRUST_PROXY=true`, and uses the
last entry, which nginx sets. The upload must start with `%PDF-`. The container runs as a
non-root user with a read-only filesystem and a 512 MB memory limit.

The in-app rate limit is per process, so more workers or containers mean separate counters.

## Keys

- `OPENAI_API_KEY` lives only in an env file on the server, readable by root only and outside
  the repo.
- Never in `VITE_*` values: they are public (see
  [0001](decisions/0001-backend-proxy-instead-of-env-token.md)).
- `.env` and `.env.*` are gitignored; only `.env.example` files are tracked.
- Run `gitleaks` before pushing.

## Logging

Per request the API logs status, duration, page count, chunk count and provider. Unhandled
errors log only the exception type. Provider errors log the error class and the status and message
returned by the provider. Document text and keys are not logged.

## Dependencies

Check from the command line:

- `npm audit` in `web/`
- `uvx pip-audit` in `api/`

Neither runs in CI (`.github/workflows` only has lint, format, typecheck, tests and build for
web, and ruff and pytest for api), so run them by hand now and then.

## Reporting issues

Open a GitHub issue. Do not put secrets, API keys or real document contents in it.
