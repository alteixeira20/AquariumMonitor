from __future__ import annotations

from fastapi import HTTPException, Request, status


def require_service(request: Request, name: str, label: str):
    service = getattr(request.app.state, name, None)
    if service is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{label} not configured",
        )
    return service
