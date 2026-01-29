from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.aquarium import Aquarium


class AquariumCreateRequest(BaseModel):
    name: str = Field(..., description="Aquarium name")
    water_type: Literal["fresh", "salt"] = Field(..., description="Water type")
    liters: float = Field(..., gt=0)
    temperature_min: float
    temperature_max: float
    ph_min: float
    ph_max: float
    tds_min: float
    tds_max: float


class AquariumResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    water_type: str
    liters: float
    temperature_min: float
    temperature_max: float
    ph_min: float
    ph_max: float
    tds_min: float
    tds_max: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, aquarium: Aquarium) -> AquariumResponse:
        return cls(
            id=aquarium.id,
            user_id=aquarium.user_id,
            name=aquarium.name,
            water_type=aquarium.water_type,
            liters=aquarium.liters,
            temperature_min=aquarium.temperature_min,
            temperature_max=aquarium.temperature_max,
            ph_min=aquarium.ph_min,
            ph_max=aquarium.ph_max,
            tds_min=aquarium.tds_min,
            tds_max=aquarium.tds_max,
            created_at=aquarium.created_at,
        )
