from __future__ import annotations

from uuid import UUID

from app.core.exceptions import DomainError
from app.domain.ph_calibration import PhCalibrationPoint
from app.domain.reading import PH_VREF
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    DeviceRepository,
    PhCalibrationRepository,
    ReadingRepository,
)
ALLOWED_PH_POINTS = {4.01, 6.86, 9.18}


def _normalize_ph_point(ph_point: float) -> float:
    return round(ph_point, 2)


class PhCalibrationService:
    def __init__(
        self,
        device_repo: DeviceRepository,
        aquarium_repo: AquariumRepository,
        aquarium_device_repo: AquariumDeviceRepository,
        reading_repo: ReadingRepository,
        calibration_repo: PhCalibrationRepository,
    ) -> None:
        self.device_repo = device_repo
        self.aquarium_repo = aquarium_repo
        self.aquarium_device_repo = aquarium_device_repo
        self.reading_repo = reading_repo
        self.calibration_repo = calibration_repo

    async def start(self, user_id: UUID, device_id: UUID) -> None:
        await self._assert_device_ready(user_id, device_id)

    async def add_point(
        self, user_id: UUID, device_id: UUID, ph_point: float, voltage: float
    ) -> PhCalibrationPoint:
        await self._assert_device_ready(user_id, device_id)
        ph_point = _normalize_ph_point(ph_point)
        if ph_point not in ALLOWED_PH_POINTS:
            raise DomainError("Invalid pH point", status_code=400, error="validation_error")
        if not 0.0 <= voltage <= PH_VREF:
            raise DomainError("Invalid voltage value", status_code=400, error="validation_error")
        return await self.calibration_repo.create_point(
            device_id=device_id,
            ph_point=ph_point,
            voltage=voltage,
            is_active=False,
        )

    async def activate(self, user_id: UUID, device_id: UUID) -> list[PhCalibrationPoint]:
        await self._assert_device_ready(user_id, device_id)
        points = await self.calibration_repo.list_latest_inactive_points_for_device(device_id)
        points_by_ph = { _normalize_ph_point(p.ph_point): p for p in points }
        if not ALLOWED_PH_POINTS.issubset(points_by_ph.keys()):
            raise DomainError(
                "Calibration requires pH 4.01, 6.86, and 9.18 points",
                status_code=400,
                error="validation_error",
            )
        selected_points = [points_by_ph[ph] for ph in sorted(ALLOWED_PH_POINTS)]
        await self.calibration_repo.deactivate_active_points(device_id)
        await self.calibration_repo.activate_points(device_id, selected_points)
        return selected_points

    async def get_current(self, user_id: UUID, device_id: UUID) -> list[PhCalibrationPoint]:
        await self._assert_device_owned(user_id, device_id)
        return await self.calibration_repo.list_active_points_for_device(device_id)

    async def _assert_device_owned(self, user_id: UUID, device_id: UUID) -> None:
        device = await self.device_repo.get(device_id)
        if device is None:
            raise DomainError("Device not found", status_code=404, error="not_found")

        if device.owner_user_id != user_id:
            raise DomainError("Device not visible", status_code=403, error="forbidden")

    async def _assert_device_ready(self, user_id: UUID, device_id: UUID) -> None:
        await self._assert_device_owned(user_id, device_id)
