from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.domain.aquarium import Aquarium
from app.domain.alert import Alert
from app.domain.device import Device
from app.domain.ph_calibration import PhCalibrationPoint
from app.domain.reading import Reading
from app.domain.user import User
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    AlertRepository,
    DeviceRepository,
    DeviceApiKeyRepository,
    PhCalibrationRepository,
    ReadingRepository,
    UserRepository,
)


class MemoryDeviceRepository(DeviceRepository):
    def __init__(self) -> None:
        self._devices: dict[UUID, Device] = {}

    async def create(
        self, name: str | None, location: str | None, owner_user_id: UUID | None
    ) -> Device:
        device = Device(name=name, location=location, owner_user_id=owner_user_id)
        if owner_user_id is not None:
            device.claimed_at = device.created_at
        self._devices[device.id] = device
        return device

    async def get(self, device_id: UUID) -> Device | None:
        return self._devices.get(device_id)

    async def list(self) -> list[Device]:
        return list(self._devices.values())

    async def update(self, device: Device) -> Device:
        self._devices[device.id] = device
        return device

    async def list_by_ids(self, device_ids: list[UUID]) -> list[Device]:
        return [self._devices[d] for d in device_ids if d in self._devices]

    async def list_for_owner(self, owner_user_id: UUID) -> list[Device]:
        return [d for d in self._devices.values() if d.owner_user_id == owner_user_id]

    async def delete(self, device_id: UUID) -> None:
        self._devices.pop(device_id, None)


class MemoryReadingRepository(ReadingRepository):
    def __init__(self) -> None:
        self._readings: list[Reading] = []

    def _filter_by_device(self, device_id: UUID) -> list[Reading]:
        return [r for r in self._readings if r.device_id == device_id]

    async def create(self, reading: Reading) -> Reading:
        self._readings.append(reading)
        return reading

    async def list(self) -> list[Reading]:
        return sorted(self._readings, key=lambda r: r.received_at, reverse=True)

    async def list_for_device(self, device_id: UUID) -> list[Reading]:
        return sorted(self._filter_by_device(device_id), key=lambda r: r.received_at, reverse=True)

    async def list_for_devices(self, device_ids: list[UUID]) -> list[Reading]:
        device_set = set(device_ids)
        readings = [r for r in self._readings if r.device_id in device_set]
        return sorted(readings, key=lambda r: r.received_at, reverse=True)

    async def list_for_device_filtered(
        self, *, device_id: UUID, from_dt: datetime | None, to_dt: datetime | None
    ) -> list[Reading]:
        readings = self._filter_by_device(device_id)
        if from_dt is not None:
            readings = [r for r in readings if r.received_at >= from_dt]
        if to_dt is not None:
            readings = [r for r in readings if r.received_at <= to_dt]
        return sorted(readings, key=lambda r: r.received_at, reverse=True)

    async def list_for_device_paginated_filtered(
        self,
        *,
        device_id: UUID,
        page: int,
        page_size: int,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> tuple[list[Reading], int]:
        all_filtered = await self.list_for_device_filtered(
            device_id=device_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        total = len(all_filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return all_filtered[start:end], total

    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Reading], int]:
        all_sorted = await self.list()
        total = len(all_sorted)
        start = (page - 1) * page_size
        end = start + page_size
        return all_sorted[start:end], total

    async def list_for_device_paginated(
        self, *, device_id: UUID, page: int, page_size: int
    ) -> tuple[list[Reading], int]:
        all_sorted = await self.list_for_device(device_id)
        total = len(all_sorted)
        start = (page - 1) * page_size
        end = start + page_size
        return all_sorted[start:end], total

    async def get_latest(self, device_id: UUID) -> Reading | None:
        readings = await self.list_for_device(device_id)
        return readings[0] if readings else None


class MemoryAlertRepository(AlertRepository):
    def __init__(self) -> None:
        self._alerts: list[Alert] = []

    async def create(self, alert: Alert) -> Alert:
        self._alerts.append(alert)
        return alert

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
    ) -> tuple[list[Alert], int]:
        alerts = self._alerts
        if aquarium_id is not None:
            alerts = [a for a in alerts if a.aquarium_id == aquarium_id]
        if alert_type is not None:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if sensor is not None:
            alerts = [a for a in alerts if a.sensor == sensor]
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if unresolved_only:
            alerts = [a for a in alerts if a.resolved_at is None]
        alerts = sorted(alerts, key=lambda a: a.created_at, reverse=True)
        total = len(alerts)
        start = (page - 1) * page_size
        end = start + page_size
        return alerts[start:end], total

    async def get_latest_for_key(
        self,
        *,
        aquarium_id: UUID,
        device_id: UUID | None,
        alert_type: str,
        sensor: str | None,
    ) -> Alert | None:
        matches = [
            alert
            for alert in self._alerts
            if alert.aquarium_id == aquarium_id
            and alert.alert_type == alert_type
            and alert.sensor == sensor
            and (alert.device_id == device_id)
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda a: a.created_at, reverse=True)[0]

    async def get_latest(self, device_id: UUID) -> Reading | None:
        readings = self._filter_by_device(device_id)
        if not readings:
            return None
        return max(readings, key=lambda r: r.received_at)


class MemoryPhCalibrationRepository(PhCalibrationRepository):
    def __init__(self) -> None:
        self._points: list[PhCalibrationPoint] = []

    async def create_point(
        self, device_id: UUID, ph_point: float, voltage: float, *, is_active: bool
    ) -> PhCalibrationPoint:
        point = PhCalibrationPoint(
            device_id=device_id,
            ph_point=ph_point,
            voltage=voltage,
            is_active=is_active,
        )
        self._points.append(point)
        return point

    async def list_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]:
        return [p for p in self._points if p.device_id == device_id]

    async def list_active_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]:
        return [p for p in self._points if p.device_id == device_id and p.is_active]

    async def list_latest_inactive_points_for_device(
        self, device_id: UUID
    ) -> list[PhCalibrationPoint]:
        latest: dict[float, PhCalibrationPoint] = {}
        for point in self._points:
            if point.device_id != device_id or point.is_active:
                continue
            existing = latest.get(point.ph_point)
            if existing is None or point.created_at > existing.created_at:
                latest[point.ph_point] = point
        return list(latest.values())

    async def deactivate_active_points(self, device_id: UUID) -> None:
        for point in self._points:
            if point.device_id == device_id and point.is_active:
                point.is_active = False

    async def activate_points(self, device_id: UUID, points: list[PhCalibrationPoint]) -> None:
        active_keys = {(p.ph_point, p.created_at) for p in points}
        for point in self._points:
            if point.device_id != device_id:
                continue
            if (point.ph_point, point.created_at) in active_keys:
                point.is_active = True


class MemoryDeviceApiKeyRepository(DeviceApiKeyRepository):
    def __init__(self) -> None:
        self._keys: dict[str, UUID] = {}
        self._revoked: set[tuple[UUID, str]] = set()

    async def create(self, device_id: UUID, key_hash: str) -> None:
        self._keys[key_hash] = device_id

    async def get_device_id_for_key(self, key_hash: str) -> UUID | None:
        device_id = self._keys.get(key_hash)
        if device_id is None:
            return None
        if (device_id, key_hash) in self._revoked:
            return None
        return device_id

    async def revoke(self, device_id: UUID, key_hash: str) -> None:
        self._revoked.add((device_id, key_hash))


class MemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users_by_id: dict[UUID, User] = {}
        self._users_by_email: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower())

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._users_by_id.get(user_id)

    async def create(self, user: User) -> User:
        self._users_by_id[user.id] = user
        self._users_by_email[user.email.lower()] = user
        return user

    async def count(self) -> int:
        return len(self._users_by_id)

    async def get_first_user(self) -> User | None:
        if not self._users_by_id:
            return None
        return min(self._users_by_id.values(), key=lambda u: u.created_at)


class MemoryAquariumRepository(AquariumRepository):
    def __init__(self) -> None:
        self._aquariums: dict[UUID, Aquarium] = {}

    async def create(self, aquarium: Aquarium) -> Aquarium:
        self._aquariums[aquarium.id] = aquarium
        return aquarium

    async def list_for_user(self, user_id: UUID) -> list[Aquarium]:
        return [a for a in self._aquariums.values() if a.user_id == user_id]

    async def get(self, aquarium_id: UUID) -> Aquarium | None:
        return self._aquariums.get(aquarium_id)

    async def update(self, aquarium: Aquarium) -> Aquarium:
        self._aquariums[aquarium.id] = aquarium
        return aquarium

    async def delete(self, aquarium_id: UUID) -> None:
        self._aquariums.pop(aquarium_id, None)


class MemoryAquariumDeviceRepository(AquariumDeviceRepository):
    def __init__(self) -> None:
        self._links: list[tuple[UUID, UUID, datetime, datetime | None]] = []

    async def attach(self, aquarium_id: UUID, device_id: UUID) -> None:
        self._links.append((device_id, aquarium_id, datetime.utcnow(), None))

    async def detach(self, aquarium_id: UUID, device_id: UUID) -> None:
        for idx, (d_id, a_id, attached_at, detached_at) in enumerate(self._links):
            if d_id == device_id and a_id == aquarium_id and detached_at is None:
                self._links[idx] = (d_id, a_id, attached_at, datetime.utcnow())

    async def get_active_aquarium_for_device(self, device_id: UUID) -> UUID | None:
        active = [link for link in self._links if link[0] == device_id and link[3] is None]
        if not active:
            return None
        active.sort(key=lambda row: row[2], reverse=True)
        return active[0][1]

    async def list_active_devices_for_aquarium(self, aquarium_id: UUID) -> list[UUID]:
        return [d_id for d_id, a_id, _, detached_at in self._links if a_id == aquarium_id and detached_at is None]

    async def list_attachment_windows_for_aquarium(
        self, aquarium_id: UUID
    ) -> list[tuple[UUID, datetime, datetime | None]]:
        windows: list[tuple[UUID, datetime, datetime | None]] = []
        for device_id, a_id, attached_at, detached_at in self._links:
            if a_id == aquarium_id:
                windows.append((device_id, attached_at, detached_at))
        windows.sort(key=lambda row: row[1])
        return windows
