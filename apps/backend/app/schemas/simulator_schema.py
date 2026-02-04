from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SimulatorDeviceRequest(BaseModel):
    device_id: UUID = Field(..., description="Device to simulate")
    aquarium_id: UUID = Field(..., description="Aquarium to attach device to")
    preset_id: str = Field(..., description="Simulation preset identifier")
