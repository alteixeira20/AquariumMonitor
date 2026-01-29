from __future__ import annotations

from uuid import UUID

from app.core.exceptions import DomainError
from app.domain.device import Device
from app.core.metrics import inc_devices_created
from app.repositories.base_repository import DeviceRepository


class DeviceService:
    """
    Application service responsible for handling device-related business logic.

    This version delegates persistence to a repository (in-memory or SQLite).
    """

    def __init__(self, repository: DeviceRepository) -> None:
        self.repository = repository

    # ----------------------------------------------------------------------
    # Create
    # ----------------------------------------------------------------------
    async def register_device(
        self,
        name: str | None = None,
        location: str | None = None,
        *,
        owner_user_id: UUID | None = None,
    ) -> Device:
        device = await self.repository.create(
            name=name, location=location, owner_user_id=owner_user_id
        )
        inc_devices_created()
        return device

    async def claim_device(self, device_id: UUID, user_id: UUID) -> Device:
        device = await self.repository.get(device_id)
        if device is None:
            raise ValueError("Device not found")
        if device.owner_user_id is not None and device.owner_user_id != user_id:
            raise DomainError(
                "Device already claimed",
                status_code=409,
                error="conflict",
            )
        if device.owner_user_id is None:
            device.claim(user_id)
            await self.repository.update(device)
        return device

    # ----------------------------------------------------------------------
    # Read
    # ----------------------------------------------------------------------
    async def get_device(self, device_id: UUID) -> Device | None:
        return await self.repository.get(device_id)

    async def list_devices(self) -> list[Device]:
        return await self.repository.list()

    async def list_devices_by_ids(self, device_ids: list[UUID]) -> list[Device]:
        return await self.repository.list_by_ids(device_ids)

    async def list_devices_for_owner(self, owner_user_id: UUID) -> list[Device]:
        return await self.repository.list_for_owner(owner_user_id)

    # ----------------------------------------------------------------------
    # Update (domain methods are already defined on Device)
    # ----------------------------------------------------------------------
    async def update_device_name(self, device_id: UUID, new_name: str) -> Device | None:
        device = await self.repository.get(device_id)
        if device:
            device.rename(new_name)
            await self.repository.update(device)
        return device

    async def update_device_location(self, device_id: UUID, new_location: str) -> Device | None:
        device = await self.repository.get(device_id)
        if device:
            device.move(new_location)
            await self.repository.update(device)
        return device

    async def deactivate_device(self, device_id: UUID) -> Device | None:
        device = await self.repository.get(device_id)
        if device:
            device.mark_inactive()
            await self.repository.update(device)
        return device
