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
    temperature_enabled: bool = Field(default=True)
    temperature_min: float
    temperature_max: float
    ph_enabled: bool = Field(default=True)
    ph_min: float
    ph_max: float
    tds_enabled: bool = Field(default=True)
    tds_min: float
    tds_max: float
    filter_type: str | None = None
    filter_flow_lph: float | None = None
    heater_watts: float | None = None
    lighting_type: str | None = None
    notes: str | None = None


class AquariumUpdateRequest(BaseModel):
    name: str = Field(..., description="Aquarium name")
    water_type: Literal["fresh", "salt"] = Field(..., description="Water type")
    liters: float = Field(..., gt=0)
    temperature_enabled: bool = Field(default=True)
    temperature_min: float
    temperature_max: float
    ph_enabled: bool = Field(default=True)
    ph_min: float
    ph_max: float
    tds_enabled: bool = Field(default=True)
    tds_min: float
    tds_max: float
    filter_type: str | None = None
    filter_flow_lph: float | None = None
    heater_watts: float | None = None
    lighting_type: str | None = None
    notes: str | None = None


class AquariumResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    water_type: str
    liters: float
    temperature_enabled: bool
    temperature_min: float
    temperature_max: float
    ph_enabled: bool
    ph_min: float
    ph_max: float
    tds_enabled: bool
    tds_min: float
    tds_max: float
    filter_type: str | None
    filter_flow_lph: float | None
    heater_watts: float | None
    lighting_type: str | None
    notes: str | None
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
            temperature_enabled=aquarium.temperature_enabled,
            temperature_min=aquarium.temperature_min,
            temperature_max=aquarium.temperature_max,
            ph_enabled=aquarium.ph_enabled,
            ph_min=aquarium.ph_min,
            ph_max=aquarium.ph_max,
            tds_enabled=aquarium.tds_enabled,
            tds_min=aquarium.tds_min,
            tds_max=aquarium.tds_max,
            filter_type=aquarium.filter_type,
            filter_flow_lph=aquarium.filter_flow_lph,
            heater_watts=aquarium.heater_watts,
            lighting_type=aquarium.lighting_type,
            notes=aquarium.notes,
            created_at=aquarium.created_at,
        )
