from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.device import Device


# ------------------------------
# Request Schema
# ------------------------------
class DeviceRegisterRequest(BaseModel):
    """
    Schema for registering a new device in the system.
    """

    name: str = Field(..., description="Human-readable device name")
    location: str | None = Field(None, description="Physical placement of the device")


# ------------------------------
# Response Schema
# ------------------------------
class DeviceResponse(BaseModel):
    """
    Full device representation returned to the client.
    """

    id: UUID
    name: str  # tests expect string, NOT optional
    location: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, d: Device) -> DeviceResponse:
        """
        Convert a domain Device object into a DeviceResponse schema.
        """
        return cls(
            id=d.id,
            name=d.name,
            location=d.location,
            is_active=d.is_active,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


class DeviceApiKeyResponse(BaseModel):
    device_id: UUID
    api_key: str


class DeviceApiKeyRevokeRequest(BaseModel):
    api_key: str = Field(..., description="Device API key to revoke")


class DeviceStatusResponse(BaseModel):
    device_id: UUID
    last_seen: datetime | None
    status: str
