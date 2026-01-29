from __future__ import annotations

from time import monotonic

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings

_RATE_LIMIT_EXEMPT_PATHS = {"/v1/health", "/v1/readiness", "/v1/metrics", "/v1/metrics/prometheus"}


def add_cors(app: FastAPI, settings: Settings) -> None:
    """Attach CORSMiddleware using settings."""
    allow_credentials = settings.allow_credentials
    if settings.cors_origins_list == ["*"]:
        allow_credentials = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=allow_credentials,
        allow_methods=settings.cors_methods_list,
        allow_headers=settings.cors_headers_list,
    )


def add_rate_limit(app: FastAPI, settings: Settings) -> None:
    if not settings.rate_limit_enabled:
        return

    window = max(1, settings.rate_limit_window_seconds)
    limit = max(1, settings.rate_limit_requests)
    state: dict[tuple[str, int], int] = {}

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        if request.url.path in _RATE_LIMIT_EXEMPT_PATHS:
            return await call_next(request)

        now = int(monotonic())
        bucket = now // window
        client = request.client.host if request.client else "unknown"
        key = (client, bucket)
        # Cleanup old buckets for this client to prevent unbounded growth.
        old_key = (client, bucket - 1)
        state.pop(old_key, None)
        count = state.get(key, 0) + 1
        state[key] = count

        if count > limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limited",
                    "message": "Rate limit exceeded",
                    "details": None,
                },
            )

        return await call_next(request)
