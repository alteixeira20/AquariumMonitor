from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Ignore because Python builds may lack datetime.UTC
# ruff: noqa: UP017


@dataclass(slots=True)
class Device:
    """
    Domain entity representing a physical IoT device (e.g., ESP32).

    - Pure business logic, no FastAPI/Pydantic/ORM.
    - UUID assigned at registration.
    - Timestamp fields are backend-generated.
    """

    id: UUID = field(default_factory=uuid4)

    # Optional metadata
    name: str | None = None
    location: str | None = None

    # Ownership
    owner_user_id: UUID | None = None
    claimed_at: datetime | None = None

    # Whether the device is active and allowed to send telemetry
    is_active: bool = True

    # Use timezone-aware timestamps (UTC)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_inactive(self) -> None:
        """Soft-deactivate the device."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def rename(self, new_name: str) -> None:
        """Rename the device (business rule)."""
        self.name = new_name
        self.updated_at = datetime.now(timezone.utc)

    def move(self, new_location: str) -> None:
        """Update device location (business rule)."""
        self.location = new_location
        self.updated_at = datetime.now(timezone.utc)

    def touch(self) -> None:
        """Refresh updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def claim(self, user_id: UUID) -> None:
        """Assign device ownership."""
        self.owner_user_id = user_id
        self.claimed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
