# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub: open the **Security** tab of this
repository and choose **Report a vulnerability** (private vulnerability reporting / security
advisories). Do not open a public issue for a vulnerability, and do not include real documents,
secrets or API keys in a report.

I will confirm the report as soon as I can and keep you updated until it is fixed.

## Supported version

Only the `main` branch (the deployed version) is supported.

## Scope

In scope:

- the web app (`web/`, served from GitHub Pages)
- the API (`api/`) and its nginx configuration (`deploy/nginx/`)

Out of scope: third-party services (GitHub, OpenAI), and findings that need a compromised
server or browser.

## Existing protections

- PDF text is treated as untrusted data: wrapped in `<document>` tags, checked for prompt
  injection, and the model output is validated on the server and again in the browser.
- Strict CORS and an `Origin` check, per-IP rate limit, and limits on file size, pages, text and
  chunks.
- Security headers on every API response and a Content-Security-Policy on the web app.
- No secrets in the frontend or in the repository; the API key lives only on the server.

Details: [docs/security.md](docs/security.md).
