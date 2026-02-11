from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import require_service
from app.core.auth import UserContext, user_context_dependency
from app.schemas.alert_schema import AlertListResponse, AlertResponse
from app.services.alert_service import AlertService


def get_alert_service(request: Request) -> AlertService:
    return require_service(request, "alert_service", "Alert service")


AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
UserContextDep = Annotated[UserContext, Depends(user_context_dependency)]

router = APIRouter()


class _AlertFilters(BaseModel):
    aquarium_id: UUID | None = Field(None)
    alert_type: str | None = Field(None)
    sensor: str | None = Field(None)
    level: int | None = Field(None, ge=0, le=3)
    unresolved_only: bool = Field(True)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    service: AlertServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_AlertFilters, Depends()],
) -> AlertListResponse:
    alerts, total = await service.list_alerts(
        aquarium_id=filters.aquarium_id,
        alert_type=filters.alert_type,
        sensor=filters.sensor,
        level=filters.level,
        unresolved_only=filters.unresolved_only,
        page=filters.page,
        page_size=filters.page_size,
    )
    return AlertListResponse(
        alerts=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        has_next=(filters.page * filters.page_size < total),
    )
