from __future__ import annotations

from collections.abc import Awaitable, Callable
import json
import logging
from logging.config import dictConfig
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.metrics import inc_request


class JsonFormatter(logging.Formatter):
    """
    Minimal JSON formatter for structured logging.

    This formatter outputs log records as JSON objects, making logs easier to
    process using centralized logging systems (e.g., ELK, Datadog, CloudWatch).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_object: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
        }

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_object)


def configure_logging(settings: Settings) -> None:
    """
    Configure logging for the entire application, including Uvicorn loggers.

    This ensures consistent formatting and log levels across:
    - FastAPI's internal logs
    - Application logs
    - Uvicorn (server) logs
    """

    log_level = settings.log_level.upper()

    if settings.log_json:
        _configure_json_logging(log_level)
    else:
        _configure_standard_logging(log_level)


def _configure_standard_logging(log_level: str) -> None:
    """Configure plain-text logging with timestamps and log levels."""

    log_format = "%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": log_format,
                    "datefmt": date_format,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "loggers": {
                "": {"handlers": ["default"], "level": log_level},
                "uvicorn.error": {"level": log_level},
                "uvicorn.access": {"handlers": ["default"], "level": log_level},
            },
        }
    )


def _configure_json_logging(log_level: str) -> None:
    """Configure structured JSON logging for production."""

    dictConfig(
        {
            "version": 1,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "loggers": {
                "": {"handlers": ["default"], "level": log_level},
                "uvicorn.error": {"level": log_level},
                "uvicorn.access": {"handlers": ["default"], "level": log_level},
            },
        }
    )


def install_request_logging(app: FastAPI) -> None:
    """
    Lightweight request logging middleware.

    Logs method, path, status, and duration. Uses whatever logger configuration
    is active (JSON or plain text).
    """

    logger = logging.getLogger("app.requests")

    @app.middleware("http")
    async def log_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = perf_counter()
        response: Response | None = None
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        try:
            response = await call_next(request)
            response.headers.setdefault("X-Request-ID", request_id)
            return response
        finally:
            duration_ms = (perf_counter() - start) * 1000
            path_params = request.scope.get("path_params") or {}

            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": getattr(response, "status_code", None),
                    "duration_ms": round(duration_ms, 2),
                    "path_params": path_params,
                    "request_id": request_id,
                },
            )
            route = request.scope.get("route")
            path_template = getattr(route, "path", request.url.path)
            inc_request(request.method, path_template, getattr(response, "status_code", None))
