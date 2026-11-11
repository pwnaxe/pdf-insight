from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Frame-Options": "DENY",
}


def apply_security_headers(headers: MutableHeaders, path: str) -> None:
    for name, value in SECURITY_HEADERS.items():
        headers[name] = value
    if path.startswith("/api/"):
        headers["Cache-Control"] = "no-store"


class SecurityHeadersMiddleware:
    # Plain ASGI so it can wrap the CORS middleware and see preflight responses too.
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                apply_security_headers(MutableHeaders(scope=message), scope["path"])
            await send(message)

        await self.app(scope, receive, send_with_headers)
