# 0001. Backend proxy instead of a token in the frontend

## Context

The web app is a static site on GitHub Pages and needs a model to analyze documents. The
simplest option is to call OpenAI from the browser with a key from an env var. Vite replaces
`import.meta.env.VITE_*` values with literals at build time, so any key set that way ends up in
the JavaScript bundle. Anyone who opens the site can read it.

## Decision

The browser never talks to OpenAI. It sends the PDF to our own API (`POST /api/analyze`), and
the API calls OpenAI. The key exists only as a server env var (`OPENAI_API_KEY`) read by
`config.py` and held as a `SecretStr`. The only `VITE_*` value is `VITE_API_URL`, which is a
public address anyway.

## Consequences

- The key cannot leak through the bundle or the repo.
- We need a server, TLS and our own abuse protection: Origin check, per-IP rate limit, nginx
  `limit_req`, size limits. See [security](../security.md).
- Text extraction and validation run on the server, so the client stays small.
- The document text passes through our server and then OpenAI.
- The API URL is public, so anyone can call it without the frontend. CORS does not prevent that.
