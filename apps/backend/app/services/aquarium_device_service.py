from __future__ import annotations

from uuid import UUID

from app.core.exceptions import DomainError
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    DeviceRepository,
    PhCalibrationRepository,
)


class AquariumDeviceService:
    def __init__(
        self,
        aquarium_repo: AquariumRepository,
        device_repo: DeviceRepository,
        association_repo: AquariumDeviceRepository,
        calibration_repo: PhCalibrationRepository,
    ) -> None:
        self.aquarium_repo = aquarium_repo
        self.device_repo = device_repo
        self.association_repo = association_repo
        self.calibration_repo = calibration_repo

    async def attach_device(self, user_id: UUID, aquarium_id: UUID, device_id: UUID) -> None:
        aquarium = await self.aquarium_repo.get(aquarium_id)
        if aquarium is None or aquarium.user_id != user_id:
            raise DomainError("Aquarium not found", status_code=404, error="not_found")

        device = await self.device_repo.get(device_id)
        if device is None:
            raise DomainError("Device not found", status_code=404, error="not_found")
        if device.owner_user_id != user_id:
            raise DomainError("Device not owned by user", status_code=403, error="forbidden")

        if not await self._has_active_calibration(device_id):
            raise DomainError(
                "Device calibration required before attachment",
                status_code=409,
                error="conflict",
            )

        active_aquarium = await self.association_repo.get_active_aquarium_for_device(device_id)
        if active_aquarium is not None:
            raise DomainError(
                "Device already attached to an aquarium",
                status_code=409,
                error="conflict",
            )

        await self.association_repo.attach(aquarium_id, device_id)

    async def _has_active_calibration(self, device_id: UUID) -> bool:
        points = await self.calibration_repo.list_active_points_for_device(device_id)
        if len(points) != 3:
            return False
        return {p.ph_point for p in points} == {4.01, 6.86, 9.18}

    async def detach_device(self, user_id: UUID, aquarium_id: UUID, device_id: UUID) -> None:
        aquarium = await self.aquarium_repo.get(aquarium_id)
        if aquarium is None or aquarium.user_id != user_id:
            raise DomainError("Aquarium not found", status_code=404, error="not_found")

        active_aquarium = await self.association_repo.get_active_aquarium_for_device(device_id)
        if active_aquarium is None:
            raise DomainError("Device is not attached", status_code=404, error="not_found")

        if active_aquarium != aquarium_id:
            raise DomainError("Device is attached to a different aquarium", status_code=409)

        await self.association_repo.detach(aquarium_id, device_id)

    async def list_devices_for_aquarium(self, user_id: UUID, aquarium_id: UUID) -> list[UUID]:
        aquarium = await self.aquarium_repo.get(aquarium_id)
        if aquarium is None or aquarium.user_id != user_id:
            raise DomainError("Aquarium not found", status_code=404, error="not_found")

        return await self.association_repo.list_active_devices_for_aquarium(aquarium_id)

    async def list_devices_for_user(self, user_id: UUID) -> list[UUID]:
        aquariums = await self.aquarium_repo.list_for_user(user_id)
        device_ids: list[UUID] = []
        seen = set()
        for aquarium in aquariums:
            for device_id in await self.association_repo.list_active_devices_for_aquarium(
                aquarium.id
            ):
                if device_id not in seen:
                    seen.add(device_id)
                    device_ids.append(device_id)
        return device_ids
