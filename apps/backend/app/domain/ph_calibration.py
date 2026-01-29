from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass(slots=True)
class PhCalibrationPoint:
    device_id: UUID
    ph_point: float
    voltage: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = False
