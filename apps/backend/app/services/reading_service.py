from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import median
from uuid import UUID

from app.core.exceptions import DomainError
from app.core.metrics import inc_readings_created
from app.domain.reading import Reading
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    DeviceRepository,
    PhCalibrationRepository,
    ReadingRepository,
)
from app.services.alert_service import AlertService


class ReadingService:
    """
    Application service responsible for:
    - Validating device existence
    - Constructing Reading domain objects
    - Running Reading.process() to compute pH + TDS
    - Persisting readings
    - Returning processed readings (with pagination support)
    """

    def __init__(
        self,
        device_repo: DeviceRepository,
        reading_repo: ReadingRepository,
        ph_calibration_repo: PhCalibrationRepository,
        aquarium_device_repo: AquariumDeviceRepository,
        aquarium_repo: AquariumRepository,
        alert_service: AlertService | None = None,
    ):
        self.device_repo = device_repo
        self.reading_repo = reading_repo
        self.ph_calibration_repo = ph_calibration_repo
        self.aquarium_device_repo = aquarium_device_repo
        self.aquarium_repo = aquarium_repo
        self.alert_service = alert_service

    # ------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------
    async def create_reading(
        self,
        *,
        device_id: UUID,
        temperature_c: float,
        raw_ph_voltage: float,
        raw_tds_voltage: float,
    ) -> Reading:
        """
        Creates and processes a reading for the given device.
        """

        # Ensure the device exists
        device = await self.device_repo.get(device_id)
        if device is None:
            raise ValueError(f"Device with ID {device_id} not found")

        # Require device is attached and calibrated
        aquarium_id = await self.aquarium_device_repo.get_active_aquarium_for_device(device_id)
        if aquarium_id is None:
            raise DomainError(
                "Device is not attached to an aquarium",
                status_code=409,
                error="conflict",
            )

        calibration_points = await self._load_active_ph_calibration(device_id)
        if calibration_points is None:
            raise DomainError(
                "Device calibration required before readings",
                status_code=409,
                error="conflict",
            )

        # Build domain reading
        reading = Reading(
            device_id=device_id,
            temperature_c=temperature_c,
            raw_ph_voltage=raw_ph_voltage,
            raw_tds_voltage=raw_tds_voltage,
        )

        # Compute derived values
        reading.process(calibration_points=calibration_points)

        # Persist
        await self.reading_repo.create(reading)
        inc_readings_created()

        # Alerts
        if self.alert_service is not None:
            await self._emit_alerts(aquarium_id, device_id, reading)

        # Return processed reading
        return reading

    async def _emit_alerts(
        self,
        aquarium_id: UUID,
        device_id: UUID,
        reading: Reading,
    ) -> None:
        aquarium = await self.aquarium_repo.get(aquarium_id)
        if aquarium is None:
            return

        def _level_for_value(value: float, min_value: float, max_value: float) -> int | None:
            if value < min_value or value > max_value:
                range_span = max_value - min_value or 1.0
                if value < min_value:
                    delta = min_value - value
                else:
                    delta = value - max_value
                percent = delta / range_span
                return 3 if percent > 0.10 else 2
            return None

        checks = [
            (
                "temperature",
                reading.temperature_c,
                aquarium.temperature_min,
                aquarium.temperature_max,
                aquarium.temperature_enabled,
                "Temperature out of range",
            ),
            (
                "ph",
                reading.ph_value,
                aquarium.ph_min,
                aquarium.ph_max,
                aquarium.ph_enabled,
                "pH out of range",
            ),
            (
                "tds",
                reading.tds_ppm,
                aquarium.tds_min,
                aquarium.tds_max,
                aquarium.tds_enabled,
                "TDS out of range",
            ),
        ]

        for sensor, value, min_value, max_value, enabled, message in checks:
            if not enabled:
                continue
            if value is None:
                await self.alert_service.create_alert_if_new(
                    aquarium_id=aquarium_id,
                    device_id=device_id,
                    alert_type="sensor_missing_data",
                    sensor=sensor,
                    level=2,
                    message=f"{sensor} reading missing",
                )
                continue
            level = _level_for_value(value, min_value, max_value)
            if level is None:
                continue
            await self.alert_service.create_alert_if_new(
                aquarium_id=aquarium_id,
                device_id=device_id,
                alert_type="sensor_out_of_range",
                sensor=sensor,
                level=level,
                message=message,
            )

    # ------------------------------------------------------------
    # Queries (non-paginated)
    # ------------------------------------------------------------
    async def list_readings(self) -> list[Reading]:
        """Return all readings, sorted by timestamp (newest first)."""
        return await self.reading_repo.list()

    async def list_readings_for_device(
        self, device_id: UUID, from_dt: datetime | None = None, to_dt: datetime | None = None
    ) -> list[Reading]:
        """Return readings for a specific device, sorted by timestamp."""
        from_dt = _normalize_datetime(from_dt)
        to_dt = _normalize_datetime(to_dt)
        if from_dt is None and to_dt is None:
            return await self.reading_repo.list_for_device(device_id)
        return await self.reading_repo.list_for_device_filtered(
            device_id=device_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )

    async def get_latest_reading(self, device_id: UUID) -> Reading | None:
        """Return the newest reading for this device, or None."""
        return await self.reading_repo.get_latest(device_id)

    # ------------------------------------------------------------
    # Queries (paginated)
    # ------------------------------------------------------------
    async def list_readings_paginated(
        self, *, page: int, page_size: int
    ) -> tuple[list[Reading], int]:
        """
        Return paginated readings and total count.
        """
        return await self.reading_repo.list_paginated(page=page, page_size=page_size)

    async def list_readings_for_device_paginated(
        self,
        *,
        device_id: UUID,
        page: int,
        page_size: int,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> tuple[list[Reading], int]:
        """
        Return paginated readings for a specific device.
        """
        from_dt = _normalize_datetime(from_dt)
        to_dt = _normalize_datetime(to_dt)
        if from_dt is None and to_dt is None:
            return await self.reading_repo.list_for_device_paginated(
                device_id=device_id, page=page, page_size=page_size
            )
        return await self.reading_repo.list_for_device_paginated_filtered(
            device_id=device_id, page=page, page_size=page_size, from_dt=from_dt, to_dt=to_dt
        )

    async def get_device_stats(
        self, *, device_id: UUID, from_dt: datetime | None = None, to_dt: datetime | None = None
    ) -> dict[str, float]:
        from_dt = _normalize_datetime(from_dt)
        to_dt = _normalize_datetime(to_dt)
        readings = await self.reading_repo.list_for_device_filtered(
            device_id=device_id, from_dt=from_dt, to_dt=to_dt
        )
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

    async def get_series(
        self,
        *,
        device_id: UUID,
        from_dt: datetime | None,
        to_dt: datetime | None,
        bucket_seconds: int,
    ) -> list[dict[str, object]]:
        bucket_seconds = max(10, bucket_seconds)
        from_dt = _normalize_datetime(from_dt)
        to_dt = _normalize_datetime(to_dt)
        if to_dt is None:
            to_dt = datetime.now(UTC)
        if from_dt is None:
            from_dt = to_dt - timedelta(hours=24)
        if from_dt > to_dt:
            raise ValueError("from must be before to")

        readings = await self.reading_repo.list_for_device_filtered(
            device_id=device_id, from_dt=from_dt, to_dt=to_dt
        )
        buckets: dict[int, list[Reading]] = {}
        for reading in readings:
            ts = _normalize_datetime(reading.received_at) or from_dt
            bucket_index = int((ts - from_dt).total_seconds() // bucket_seconds)
            buckets.setdefault(bucket_index, []).append(reading)

        points: list[dict[str, object]] = []
        for index in sorted(buckets.keys()):
            bucket_readings = buckets[index]
            temps = [r.temperature_c for r in bucket_readings]
            phs = [r.ph_value for r in bucket_readings if r.ph_value is not None]
            tds = [r.tds_ppm for r in bucket_readings if r.tds_ppm is not None]
            if not temps or not phs or not tds:
                continue
            bucket_start = from_dt + timedelta(seconds=bucket_seconds * index)
            points.append(
                {
                    "bucket_start": bucket_start,
                    "temperature_median": float(median(temps)),
                    "ph_median": float(median(phs)),
                    "tds_median": float(median(tds)),
                    "count": len(bucket_readings),
                }
            )
        return points

    async def _load_active_ph_calibration(
        self, device_id: UUID
    ) -> list[tuple[float, float]] | None:
        points = await self.ph_calibration_repo.list_active_points_for_device(device_id)
        if len(points) != 3:
            return None
        ph_points = {point.ph_point for point in points}
        if ph_points != {4.01, 6.86, 9.18}:
            return None
        calibration_points: list[tuple[float, float]] = []
        for point in points:
            calibration_points.append((point.ph_point, point.voltage))
        return calibration_points


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
