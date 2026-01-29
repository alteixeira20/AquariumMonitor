from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """
    Custom exception for domain/service layer.

    Allows returning a specific HTTP status and error code.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error: str = "domain_error",
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error
        self.details = details


def _error_payload(*, error: str, message: str, details: object | None = None) -> dict[str, object]:
    return {"error": error, "message": message, "details": details}


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(error=exc.error, message=exc.message, details=exc.details),
    )


def _http_error_code(status_code: int) -> str:
    if status_code == status.HTTP_404_NOT_FOUND:
        return "not_found"
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        return "validation_error"
    if status_code >= 500:
        return "internal_error"
    return "bad_request"


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    error_code = _http_error_code(exc.status_code)
    message = exc.detail or "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(error=error_code, message=str(message)),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=_error_payload(
            error="validation_error",
            message="Invalid request",
            details=exc.errors(),
        ),
    )


async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_error_payload(error="value_error", message=str(exc)),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(error="internal_error", message="Unexpected error"),
    )
