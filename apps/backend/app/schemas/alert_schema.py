from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    id: UUID
    aquarium_id: UUID
    device_id: UUID | None
    alert_type: str
    sensor: str | None
    level: int = Field(..., ge=0, le=3)
    message: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
