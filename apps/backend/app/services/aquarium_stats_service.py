from __future__ import annotations

from datetime import UTC, datetime
from statistics import median
from uuid import UUID

from app.core.exceptions import DomainError
from app.domain.reading import Reading
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    ReadingRepository,
)


class AquariumStatsService:
    def __init__(
        self,
        aquarium_repo: AquariumRepository,
        aquarium_device_repo: AquariumDeviceRepository,
        reading_repo: ReadingRepository,
    ) -> None:
        self.aquarium_repo = aquarium_repo
        self.aquarium_device_repo = aquarium_device_repo
        self.reading_repo = reading_repo

    async def get_stats(
        self,
        *,
        user_id: UUID,
        aquarium_id: UUID,
        device_id: UUID | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> dict[str, float]:
        aquarium = await self.aquarium_repo.get(aquarium_id)
        if aquarium is None or aquarium.user_id != user_id:
            raise DomainError("Aquarium not found", status_code=404, error="not_found")

        if device_id is not None:
            active_aquarium = await self.aquarium_device_repo.get_active_aquarium_for_device(
                device_id
            )
            if active_aquarium != aquarium_id:
                raise DomainError("Device not attached to aquarium", status_code=404)

        windows = await self.aquarium_device_repo.list_attachment_windows_for_aquarium(aquarium_id)
        if device_id is not None:
            windows = [window for window in windows if window[0] == device_id]

        readings: list[Reading] = []
        for window_device_id, attached_at, detached_at in windows:
            window_start = _normalize_datetime(attached_at)
            window_end = _normalize_datetime(detached_at)
            effective_from = _max_datetime(window_start, _normalize_datetime(from_dt))
            effective_to = _min_datetime(window_end, _normalize_datetime(to_dt))
            window_readings = await self.reading_repo.list_for_device_filtered(
                device_id=window_device_id,
                from_dt=effective_from,
                to_dt=effective_to,
            )
            if window_end is not None:
                cutoff = window_end
                window_readings = [
                    reading
                    for reading in window_readings
                    if _normalize_datetime(reading.received_at) < cutoff
                ]
            readings.extend(window_readings)
        if not readings:
            raise DomainError("No readings available", status_code=404, error="not_found")

        temps = [r.temperature_c for r in readings]
        phs = [r.ph_value for r in readings if r.ph_value is not None]
        tds = [r.tds_ppm for r in readings if r.tds_ppm is not None]

        if not temps or not phs or not tds:
            raise DomainError("No readings available", status_code=404, error="not_found")

        return {
            "temperature_median": float(median(temps)),
            "ph_median": float(median(phs)),
            "tds_median": float(median(tds)),
        }


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _max_datetime(a: datetime | None, b: datetime | None) -> datetime | None:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def _min_datetime(a: datetime | None, b: datetime | None) -> datetime | None:
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)
