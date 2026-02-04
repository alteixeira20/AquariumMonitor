from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.aquarium import Aquarium
from app.domain.device import Device
from app.domain.ph_calibration import PhCalibrationPoint
from app.domain.reading import Reading
from app.domain.user import User
from app.infrastructure.db_models import (
    AquariumDeviceModel,
    AquariumModel,
    DeviceApiKeyModel,
    DeviceModel,
    DevicePhCalibrationModel,
    ReadingModel,
    UserModel,
)
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    DeviceApiKeyRepository,
    DeviceRepository,
    PhCalibrationRepository,
    ReadingRepository,
    UserRepository,
)


class MariaDbDeviceRepository(DeviceRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(
        self, name: str | None, location: str | None, owner_user_id: UUID | None
    ) -> Device:
        device_id = uuid4()
        now = datetime.utcnow()
        model = DeviceModel(
            id=str(device_id),
            name=name,
            location=location,
            owner_user_id=str(owner_user_id) if owner_user_id is not None else None,
            claimed_at=now if owner_user_id is not None else None,
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()

        return Device(
            id=device_id,
            name=name,
            location=location,
            owner_user_id=owner_user_id,
            claimed_at=now if owner_user_id is not None else None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    async def get(self, device_id: UUID) -> Device | None:
        async with self._session_factory() as session:
            model = await session.get(DeviceModel, str(device_id))
            if model is None:
                return None
            return Device(
                id=UUID(model.id),
                name=model.name,
                location=model.location,
                owner_user_id=UUID(model.owner_user_id) if model.owner_user_id else None,
                claimed_at=model.claimed_at,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )

    async def list(self) -> list[Device]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(DeviceModel).order_by(DeviceModel.created_at.desc())
            )
            models = result.scalars().all()
            return [
                Device(
                    id=UUID(m.id),
                    name=m.name,
                    location=m.location,
                    owner_user_id=UUID(m.owner_user_id) if m.owner_user_id else None,
                    claimed_at=m.claimed_at,
                    is_active=m.is_active,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in models
            ]

    async def update(self, device: Device) -> Device:
        async with self._session_factory() as session:
            await session.execute(
                update(DeviceModel)
                .where(DeviceModel.id == str(device.id))
                .values(
                    name=device.name,
                    location=device.location,
                    owner_user_id=str(device.owner_user_id) if device.owner_user_id else None,
                    claimed_at=device.claimed_at.replace(tzinfo=None)
                    if device.claimed_at
                    else None,
                    is_active=device.is_active,
                    updated_at=device.updated_at.replace(tzinfo=None),
                )
            )
            await session.commit()
        return device

    async def list_by_ids(self, device_ids: list[UUID]) -> list[Device]:
        if not device_ids:
            return []
        device_list = [str(d) for d in device_ids]
        async with self._session_factory() as session:
            result = await session.execute(
                select(DeviceModel)
                .where(DeviceModel.id.in_(device_list))
                .order_by(DeviceModel.created_at.desc())
            )
            models = result.scalars().all()
            return [
                Device(
                    id=UUID(m.id),
                    name=m.name,
                    location=m.location,
                    owner_user_id=UUID(m.owner_user_id) if m.owner_user_id else None,
                    claimed_at=m.claimed_at,
                    is_active=m.is_active,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in models
            ]

    async def list_for_owner(self, owner_user_id: UUID) -> list[Device]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(DeviceModel)
                .where(DeviceModel.owner_user_id == str(owner_user_id))
                .order_by(DeviceModel.created_at.desc())
            )
            models = result.scalars().all()
            return [
                Device(
                    id=UUID(m.id),
                    name=m.name,
                    location=m.location,
                    owner_user_id=UUID(m.owner_user_id) if m.owner_user_id else None,
                    claimed_at=m.claimed_at,
                    is_active=m.is_active,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in models
            ]

    async def delete(self, device_id: UUID) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(ReadingModel).where(ReadingModel.device_id == str(device_id))
            )
            await session.execute(
                delete(DeviceApiKeyModel).where(
                    DeviceApiKeyModel.device_id == str(device_id)
                )
            )
            await session.execute(
                delete(DevicePhCalibrationModel).where(
                    DevicePhCalibrationModel.device_id == str(device_id)
                )
            )
            await session.execute(
                delete(AquariumDeviceModel).where(
                    AquariumDeviceModel.device_id == str(device_id)
                )
            )
            await session.execute(
                delete(DeviceModel).where(DeviceModel.id == str(device_id))
            )
            await session.commit()


class MariaDbReadingRepository(ReadingRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, reading: Reading) -> Reading:
        model = ReadingModel(
            device_id=str(reading.device_id),
            temperature_c=reading.temperature_c,
            raw_ph_voltage=reading.raw_ph_voltage,
            raw_tds_voltage=reading.raw_tds_voltage,
            ph_value=reading.ph_value,
            tds_ppm=reading.tds_ppm,
            ph_calibrated=reading.ph_calibrated,
            received_at=reading.received_at,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return reading

    async def list(self) -> list[Reading]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReadingModel).order_by(ReadingModel.received_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models]

    async def list_for_device(self, device_id: UUID) -> list[Reading]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReadingModel)
                .where(ReadingModel.device_id == str(device_id))
                .order_by(ReadingModel.received_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models]

    async def list_for_devices(self, device_ids: list[UUID]) -> list[Reading]:
        if not device_ids:
            return []
        device_list = [str(d) for d in device_ids]
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReadingModel)
                .where(ReadingModel.device_id.in_(device_list))
                .order_by(ReadingModel.received_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models]

    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Reading], int]:
        async with self._session_factory() as session:
            total = await session.scalar(select(func.count()).select_from(ReadingModel))
            offset = (page - 1) * page_size
            result = await session.execute(
                select(ReadingModel)
                .order_by(ReadingModel.received_at.desc())
                .limit(page_size)
                .offset(offset)
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models], int(total or 0)

    async def list_for_device_filtered(
        self,
        *,
        device_id: UUID,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> list[Reading]:
        conditions = [ReadingModel.device_id == str(device_id)]
        if from_dt is not None:
            conditions.append(ReadingModel.received_at >= _normalize_dt(from_dt))
        if to_dt is not None:
            conditions.append(ReadingModel.received_at <= _normalize_dt(to_dt))
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReadingModel).where(*conditions).order_by(ReadingModel.received_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models]

    async def list_for_device_paginated_filtered(
        self,
        *,
        device_id: UUID,
        page: int,
        page_size: int,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> tuple[list[Reading], int]:
        conditions = [ReadingModel.device_id == str(device_id)]
        if from_dt is not None:
            conditions.append(ReadingModel.received_at >= _normalize_dt(from_dt))
        if to_dt is not None:
            conditions.append(ReadingModel.received_at <= _normalize_dt(to_dt))
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count()).select_from(ReadingModel).where(*conditions)
            )
            offset = (page - 1) * page_size
            result = await session.execute(
                select(ReadingModel)
                .where(*conditions)
                .order_by(ReadingModel.received_at.desc())
                .limit(page_size)
                .offset(offset)
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models], int(total or 0)

    async def list_for_device_paginated(
        self, *, device_id: UUID, page: int, page_size: int
    ) -> tuple[list[Reading], int]:
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count())
                .select_from(ReadingModel)
                .where(ReadingModel.device_id == str(device_id))
            )
            offset = (page - 1) * page_size
            result = await session.execute(
                select(ReadingModel)
                .where(ReadingModel.device_id == str(device_id))
                .order_by(ReadingModel.received_at.desc())
                .limit(page_size)
                .offset(offset)
            )
            models = result.scalars().all()
            return [_model_to_reading(m) for m in models], int(total or 0)

    async def get_latest(self, device_id: UUID) -> Reading | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReadingModel)
                .where(ReadingModel.device_id == str(device_id))
                .order_by(ReadingModel.received_at.desc())
                .limit(1)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return _model_to_reading(model)


class MariaDbUserRepository(UserRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_email(self, email: str) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == email))
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return _model_to_user(model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        async with self._session_factory() as session:
            model = await session.get(UserModel, str(user_id))
            if model is None:
                return None
            return _model_to_user(model)

    async def create(self, user: User) -> User:
        model = UserModel(
            id=str(user.id),
            email=user.email,
            password_hash=user.password_hash,
            is_active=user.is_active,
            created_at=user.created_at.replace(tzinfo=None),
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return user

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(func.count(UserModel.id)))
            return int(result.scalar() or 0)

    async def get_first_user(self) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).order_by(UserModel.created_at.asc()).limit(1)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return _model_to_user(model)


class MariaDbAquariumRepository(AquariumRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, aquarium: Aquarium) -> Aquarium:
        model = AquariumModel(
            id=str(aquarium.id),
            user_id=str(aquarium.user_id),
            name=aquarium.name,
            water_type=aquarium.water_type,
            liters=aquarium.liters,
            temperature_enabled=aquarium.temperature_enabled,
            temperature_min=aquarium.temperature_min,
            temperature_max=aquarium.temperature_max,
            ph_enabled=aquarium.ph_enabled,
            ph_min=aquarium.ph_min,
            ph_max=aquarium.ph_max,
            tds_enabled=aquarium.tds_enabled,
            tds_min=aquarium.tds_min,
            tds_max=aquarium.tds_max,
            filter_type=aquarium.filter_type,
            filter_flow_lph=aquarium.filter_flow_lph,
            heater_watts=aquarium.heater_watts,
            lighting_type=aquarium.lighting_type,
            notes=aquarium.notes,
            created_at=aquarium.created_at.replace(tzinfo=None),
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return aquarium

    async def list_for_user(self, user_id: UUID) -> list[Aquarium]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AquariumModel)
                .where(AquariumModel.user_id == str(user_id))
                .order_by(AquariumModel.created_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_aquarium(m) for m in models]

    async def get(self, aquarium_id: UUID) -> Aquarium | None:
        async with self._session_factory() as session:
            model = await session.get(AquariumModel, str(aquarium_id))
            if model is None:
                return None
            return _model_to_aquarium(model)

    async def update(self, aquarium: Aquarium) -> Aquarium:
        async with self._session_factory() as session:
            await session.execute(
                update(AquariumModel)
                .where(AquariumModel.id == str(aquarium.id))
                .values(
                    name=aquarium.name,
                    water_type=aquarium.water_type,
                    liters=aquarium.liters,
                    temperature_enabled=aquarium.temperature_enabled,
                    temperature_min=aquarium.temperature_min,
                    temperature_max=aquarium.temperature_max,
                    ph_enabled=aquarium.ph_enabled,
                    ph_min=aquarium.ph_min,
                    ph_max=aquarium.ph_max,
                    tds_enabled=aquarium.tds_enabled,
                    tds_min=aquarium.tds_min,
                    tds_max=aquarium.tds_max,
                    filter_type=aquarium.filter_type,
                    filter_flow_lph=aquarium.filter_flow_lph,
                    heater_watts=aquarium.heater_watts,
                    lighting_type=aquarium.lighting_type,
                    notes=aquarium.notes,
                )
            )
            await session.commit()
        return aquarium

    async def delete(self, aquarium_id: UUID) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(AquariumDeviceModel).where(
                    AquariumDeviceModel.aquarium_id == str(aquarium_id)
                )
            )
            await session.execute(
                delete(AquariumModel).where(AquariumModel.id == str(aquarium_id))
            )
            await session.commit()


class MariaDbAquariumDeviceRepository(AquariumDeviceRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def attach(self, aquarium_id: UUID, device_id: UUID) -> None:
        model = AquariumDeviceModel(
            aquarium_id=str(aquarium_id),
            device_id=str(device_id),
            attached_at=datetime.utcnow(),
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()

    async def detach(self, aquarium_id: UUID, device_id: UUID) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(AquariumDeviceModel)
                .where(
                    AquariumDeviceModel.aquarium_id == str(aquarium_id),
                    AquariumDeviceModel.device_id == str(device_id),
                    AquariumDeviceModel.detached_at.is_(None),
                )
                .values(detached_at=datetime.utcnow())
            )
            await session.commit()

    async def get_active_aquarium_for_device(self, device_id: UUID) -> UUID | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AquariumDeviceModel.aquarium_id)
                .where(
                    AquariumDeviceModel.device_id == str(device_id),
                    AquariumDeviceModel.detached_at.is_(None),
                )
                .order_by(AquariumDeviceModel.attached_at.desc())
                .limit(1)
            )
            row = result.first()
            if row is None:
                return None
            return UUID(row[0])

    async def list_active_devices_for_aquarium(self, aquarium_id: UUID) -> list[UUID]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AquariumDeviceModel.device_id).where(
                    AquariumDeviceModel.aquarium_id == str(aquarium_id),
                    AquariumDeviceModel.detached_at.is_(None),
                )
            )
            rows = result.all()
            return [UUID(row[0]) for row in rows]

    async def list_attachment_windows_for_aquarium(
        self, aquarium_id: UUID
    ) -> list[tuple[UUID, datetime, datetime | None]]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(
                    AquariumDeviceModel.device_id,
                    AquariumDeviceModel.attached_at,
                    AquariumDeviceModel.detached_at,
                )
                .where(AquariumDeviceModel.aquarium_id == str(aquarium_id))
                .order_by(AquariumDeviceModel.attached_at.asc())
            )
            rows = result.all()
            return [(UUID(row[0]), row[1], row[2]) for row in rows]


class MariaDbDeviceApiKeyRepository(DeviceApiKeyRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, device_id: UUID, key_hash: str) -> None:
        model = DeviceApiKeyModel(
            device_id=str(device_id),
            key_hash=key_hash,
            created_at=datetime.utcnow(),
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()

    async def get_device_id_for_key(self, key_hash: str) -> UUID | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(DeviceApiKeyModel.device_id)
                .where(
                    DeviceApiKeyModel.key_hash == key_hash,
                    DeviceApiKeyModel.revoked_at.is_(None),
                )
                .limit(1)
            )
            row = result.first()
            if row is None:
                return None
            return UUID(row[0])

    async def revoke(self, device_id: UUID, key_hash: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(DeviceApiKeyModel)
                .where(
                    DeviceApiKeyModel.device_id == str(device_id),
                    DeviceApiKeyModel.key_hash == key_hash,
                    DeviceApiKeyModel.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.utcnow())
            )
            await session.commit()


class MariaDbPhCalibrationRepository(PhCalibrationRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create_point(
        self, device_id: UUID, ph_point: float, voltage: float, *, is_active: bool
    ) -> PhCalibrationPoint:
        model = DevicePhCalibrationModel(
            device_id=str(device_id),
            ph_point=ph_point,
            voltage=voltage,
            is_active=is_active,
            created_at=datetime.utcnow(),
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return _model_to_ph_calibration(model)

    async def list_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(DevicePhCalibrationModel)
                .where(DevicePhCalibrationModel.device_id == str(device_id))
                .order_by(DevicePhCalibrationModel.created_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_ph_calibration(m) for m in models]

    async def list_active_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(DevicePhCalibrationModel)
                .where(
                    DevicePhCalibrationModel.device_id == str(device_id),
                    DevicePhCalibrationModel.is_active.is_(True),
                )
                .order_by(DevicePhCalibrationModel.created_at.desc())
            )
            models = result.scalars().all()
            return [_model_to_ph_calibration(m) for m in models]

    async def list_latest_inactive_points_for_device(
        self, device_id: UUID
    ) -> list[PhCalibrationPoint]:
        async with self._session_factory() as session:
            latest_ids_subq = (
                select(func.max(DevicePhCalibrationModel.id).label("id"))
                .where(
                    DevicePhCalibrationModel.device_id == str(device_id),
                    DevicePhCalibrationModel.is_active.is_(False),
                )
                .group_by(DevicePhCalibrationModel.ph_point)
                .subquery()
            )
            result = await session.execute(
                select(DevicePhCalibrationModel).where(
                    DevicePhCalibrationModel.id.in_(select(latest_ids_subq.c.id))
                )
            )
            models = result.scalars().all()
            return [_model_to_ph_calibration(m) for m in models]

    async def deactivate_active_points(self, device_id: UUID) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(DevicePhCalibrationModel)
                .where(
                    DevicePhCalibrationModel.device_id == str(device_id),
                    DevicePhCalibrationModel.is_active.is_(True),
                )
                .values(is_active=False)
            )
            await session.commit()

    async def activate_points(self, device_id: UUID, points: list[PhCalibrationPoint]) -> None:
        if not points:
            return
        async with self._session_factory() as session:
            await session.execute(
                update(DevicePhCalibrationModel)
                .where(
                    DevicePhCalibrationModel.device_id == str(device_id),
                    DevicePhCalibrationModel.created_at.in_([p.created_at for p in points]),
                    DevicePhCalibrationModel.ph_point.in_([p.ph_point for p in points]),
                )
                .values(is_active=True)
            )
            await session.commit()


def _model_to_reading(model: ReadingModel) -> Reading:
    return Reading(
        device_id=UUID(model.device_id),
        temperature_c=model.temperature_c,
        raw_ph_voltage=model.raw_ph_voltage,
        raw_tds_voltage=model.raw_tds_voltage,
        ph_value=model.ph_value,
        tds_ppm=model.tds_ppm,
        ph_calibrated=model.ph_calibrated,
        received_at=model.received_at,
    )


def _model_to_user(model: UserModel) -> User:
    return User(
        id=UUID(model.id),
        email=model.email,
        password_hash=model.password_hash,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def _model_to_aquarium(model: AquariumModel) -> Aquarium:
    return Aquarium(
        id=UUID(model.id),
        user_id=UUID(model.user_id),
        name=model.name,
        water_type=model.water_type,
        liters=model.liters,
        temperature_enabled=model.temperature_enabled,
        temperature_min=model.temperature_min,
        temperature_max=model.temperature_max,
        ph_enabled=model.ph_enabled,
        ph_min=model.ph_min,
        ph_max=model.ph_max,
        tds_enabled=model.tds_enabled,
        tds_min=model.tds_min,
        tds_max=model.tds_max,
        filter_type=model.filter_type,
        filter_flow_lph=model.filter_flow_lph,
        heater_watts=model.heater_watts,
        lighting_type=model.lighting_type,
        notes=model.notes,
        created_at=model.created_at,
    )


def _model_to_ph_calibration(model: DevicePhCalibrationModel) -> PhCalibrationPoint:
    return PhCalibrationPoint(
        device_id=UUID(model.device_id),
        ph_point=model.ph_point,
        voltage=model.voltage,
        created_at=model.created_at,
        is_active=model.is_active,
    )


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
