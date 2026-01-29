from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response


def add_security_headers(app: FastAPI) -> None:
    """Simple middleware to add common security headers."""

    @app.middleware("http")
    async def set_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:  # type: ignore[func-returns-value]
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        return response
