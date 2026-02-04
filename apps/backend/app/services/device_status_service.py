from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.exceptions import DomainError
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    ReadingRepository,
)

OFFLINE_THRESHOLD_SECONDS = 180


class DeviceStatusService:
    def __init__(
        self,
        aquarium_repo: AquariumRepository,
        aquarium_device_repo: AquariumDeviceRepository,
        reading_repo: ReadingRepository,
    ) -> None:
        self.aquarium_repo = aquarium_repo
        self.aquarium_device_repo = aquarium_device_repo
        self.reading_repo = reading_repo

    async def get_status(self, user_id: UUID, device_id: UUID) -> dict[str, object]:
        aquarium_id = await self.aquarium_device_repo.get_active_aquarium_for_device(device_id)
        if aquarium_id is None:
            raise DomainError("Device not attached", status_code=404, error="not_found")

        aquarium = await self.aquarium_repo.get(aquarium_id)
        if aquarium is None or aquarium.user_id != user_id:
            raise DomainError("Device not found", status_code=404, error="not_found")

        reading = await self.reading_repo.get_latest(device_id)
        last_seen = reading.received_at if reading is not None else None
        last_seen = _normalize_datetime(last_seen)

        status = "offline"
        if last_seen is not None:
            now = datetime.now(UTC)
            if now - last_seen <= timedelta(seconds=OFFLINE_THRESHOLD_SECONDS):
                status = "online"

        return {
            "device_id": device_id,
            "last_seen": last_seen,
            "status": status,
        }


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
