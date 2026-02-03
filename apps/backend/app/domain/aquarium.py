from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

# ruff: noqa: UP017


@dataclass(slots=True)
class Aquarium:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    name: str = ""
    water_type: str = "fresh"
    liters: float = 0.0
    temperature_enabled: bool = True
    temperature_min: float = 0.0
    temperature_max: float = 0.0
    ph_enabled: bool = True
    ph_min: float = 0.0
    ph_max: float = 14.0
    tds_enabled: bool = True
    tds_min: float = 0.0
    tds_max: float = 0.0
    filter_type: str | None = None
    filter_flow_lph: float | None = None
    heater_watts: float | None = None
    lighting_type: str | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
