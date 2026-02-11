from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Alert:
    aquarium_id: UUID
    device_id: UUID | None
    alert_type: str
    sensor: str | None
    level: int
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)
