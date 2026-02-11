from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.aquarium import Aquarium
from app.domain.alert import Alert
from app.domain.device import Device
from app.domain.ph_calibration import PhCalibrationPoint
from app.domain.reading import Reading
from app.domain.user import User


class DeviceRepository(ABC):
    @abstractmethod
    async def create(
        self, name: str | None, location: str | None, owner_user_id: UUID | None
    ) -> Device: ...

    @abstractmethod
    async def get(self, device_id: UUID) -> Device | None: ...

    @abstractmethod
    async def list(self) -> list[Device]: ...

    @abstractmethod
    async def update(self, device: Device) -> Device: ...

    @abstractmethod
    async def list_by_ids(self, device_ids: list[UUID]) -> list[Device]: ...

    @abstractmethod
    async def list_for_owner(self, owner_user_id: UUID) -> list[Device]: ...

    @abstractmethod
    async def delete(self, device_id: UUID) -> None: ...


class ReadingRepository(ABC):
    @abstractmethod
    async def create(self, reading: Reading) -> Reading: ...

    @abstractmethod
    async def list(self) -> list[Reading]: ...

    @abstractmethod
    async def list_for_device(self, device_id: UUID) -> list[Reading]: ...

    @abstractmethod
    async def list_for_devices(self, device_ids: list[UUID]) -> list[Reading]: ...

    @abstractmethod
    async def list_for_device_filtered(
        self,
        *,
        device_id: UUID,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> list[Reading]: ...

    @abstractmethod
    async def list_for_device_paginated_filtered(
        self,
        *,
        device_id: UUID,
        page: int,
        page_size: int,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> tuple[list[Reading], int]: ...

    @abstractmethod
    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Reading], int]: ...

    @abstractmethod
    async def list_for_device_paginated(
        self, *, device_id: UUID, page: int, page_size: int
    ) -> tuple[list[Reading], int]: ...

    @abstractmethod
    async def get_latest(self, device_id: UUID) -> Reading | None: ...


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def get_first_user(self) -> User | None: ...


class AquariumRepository(ABC):
    @abstractmethod
    async def create(self, aquarium: Aquarium) -> Aquarium: ...

    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[Aquarium]: ...

    @abstractmethod
    async def get(self, aquarium_id: UUID) -> Aquarium | None: ...

    @abstractmethod
    async def update(self, aquarium: Aquarium) -> Aquarium: ...

    @abstractmethod
    async def delete(self, aquarium_id: UUID) -> None: ...


class AquariumDeviceRepository(ABC):
    @abstractmethod
    async def attach(self, aquarium_id: UUID, device_id: UUID) -> None: ...

    @abstractmethod
    async def detach(self, aquarium_id: UUID, device_id: UUID) -> None: ...

    @abstractmethod
    async def get_active_aquarium_for_device(self, device_id: UUID) -> UUID | None: ...

    @abstractmethod
    async def list_active_devices_for_aquarium(self, aquarium_id: UUID) -> list[UUID]: ...

    @abstractmethod
    async def list_attachment_windows_for_aquarium(
        self, aquarium_id: UUID
    ) -> list[tuple[UUID, datetime, datetime | None]]: ...


class DeviceApiKeyRepository(ABC):
    @abstractmethod
    async def create(self, device_id: UUID, key_hash: str) -> None: ...

    @abstractmethod
    async def get_device_id_for_key(self, key_hash: str) -> UUID | None: ...

    @abstractmethod
    async def revoke(self, device_id: UUID, key_hash: str) -> None: ...


class PhCalibrationRepository(ABC):
    @abstractmethod
    async def create_point(
        self, device_id: UUID, ph_point: float, voltage: float, *, is_active: bool
    ) -> PhCalibrationPoint: ...

    @abstractmethod
    async def list_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]: ...

    @abstractmethod
    async def list_active_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]: ...

    @abstractmethod
    async def list_latest_inactive_points_for_device(
        self, device_id: UUID
    ) -> list[PhCalibrationPoint]: ...

    @abstractmethod
    async def deactivate_active_points(self, device_id: UUID) -> None: ...

    @abstractmethod
    async def activate_points(self, device_id: UUID, points: list[PhCalibrationPoint]) -> None: ...


class AlertRepository(ABC):
    @abstractmethod
    async def create(self, alert: Alert) -> Alert: ...

    @abstractmethod
    async def list(
        self,
        *,
        aquarium_id: UUID | None,
        alert_type: str | None,
        sensor: str | None,
        level: int | None,
        unresolved_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Alert], int]: ...

    @abstractmethod
    async def get_latest_for_key(
        self,
        *,
        aquarium_id: UUID,
        device_id: UUID | None,
        alert_type: str,
        sensor: str | None,
    ) -> Alert | None: ...
