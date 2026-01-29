from __future__ import annotations

from fastapi import APIRouter, status

# Router specific to all Event-related endpoints
router = APIRouter()


@router.get(
    "/events",
    summary="List events",
    status_code=status.HTTP_200_OK,
)
async def list_events() -> dict[str, str]:
    """
    Temporary placeholder endpoint for Events API.

    This endpoint will later be replaced by a full implementation that includes:
    - domain models
    - request/response schemas
    - repository layer (SQLite)
    - service layer (business logic)

    For now, it simply confirms the routing is functional.
    """
    return {"message": "Events endpoint is working"}
