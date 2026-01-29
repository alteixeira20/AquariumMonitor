from __future__ import annotations

from pathlib import Path
from uuid import UUID

import aiosqlite
import pytest

from app.domain.aquarium import Aquarium
from app.repositories.sqlite_repository import (
    SqliteAquariumDeviceRepository,
    SqliteAquariumRepository,
    SqliteDeviceRepository,
    SqlitePhCalibrationRepository,
    SqliteReadingRepository,
    init_db,
)
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.aquarium_service import AquariumService
from app.services.device_service import DeviceService
from app.services.reading_service import ReadingService


@pytest.mark.sqlite_only
@pytest.mark.asyncio
async def test_persistence_across_connections(tmp_path: Path):
    db_path = tmp_path / "persist_me.db"

    # First connection: create schema, add data
    (
        device_service_1,
        reading_service_1,
        aquarium_service_1,
        aquarium_device_service_1,
        calibration_repo_1,
        conn1,
    ) = await _services_from_path(db_path)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    aquarium = await aquarium_service_1.create_aquarium(
        Aquarium(
            user_id=owner_id,
            name="Persisted Tank",
            water_type="fresh",
            liters=80,
            temperature_min=22,
            temperature_max=26,
            ph_min=6.5,
            ph_max=7.5,
            tds_min=150,
            tds_max=350,
        )
    )
    device = await device_service_1.register_device(
        name="Persisted", location=None, owner_user_id=owner_id
    )
    await calibration_repo_1.create_point(
        device_id=device.id, ph_point=4.01, voltage=3.0, is_active=True
    )
    await calibration_repo_1.create_point(
        device_id=device.id, ph_point=6.86, voltage=2.5, is_active=True
    )
    await calibration_repo_1.create_point(
        device_id=device.id, ph_point=9.18, voltage=2.0, is_active=True
    )
    await aquarium_device_service_1.attach_device(owner_id, aquarium.id, device.id)
    await reading_service_1.create_reading(
        device_id=device.id,
        temperature_c=25,
        raw_ph_voltage=2.5,
        raw_tds_voltage=1.0,
    )
    await conn1.close()

    # Simulate restart by creating new services/connections
    (
        device_service_2,
        reading_service_2,
        _aquarium_service_2,
        _aquarium_device_service_2,
        _calibration_repo_2,
        conn2,
    ) = await _services_from_path(db_path)
    fetched = await device_service_2.get_device(device.id)
    readings = await reading_service_2.list_readings_for_device(device.id)

    assert fetched is not None
    assert fetched.name == "Persisted"
    assert any(
        (UUID(r.device_id) if isinstance(r.device_id, str) else r.device_id) == device.id
        for r in readings
    )
    await conn2.close()


async def _services_from_path(db_path: Path):
    conn = await aiosqlite.connect(db_path)
    await init_db(db_path, conn)

    device_repo = SqliteDeviceRepository(conn)
    reading_repo = SqliteReadingRepository(conn)
    calibration_repo = SqlitePhCalibrationRepository(conn)
    aquarium_repo = SqliteAquariumRepository(conn)
    aquarium_device_repo = SqliteAquariumDeviceRepository(conn)

    device_service = DeviceService(device_repo)
    reading_service = ReadingService(
        device_repo, reading_repo, calibration_repo, aquarium_device_repo
    )
    aquarium_service = AquariumService(aquarium_repo)
    aquarium_device_service = AquariumDeviceService(
        aquarium_repo, device_repo, aquarium_device_repo, calibration_repo
    )

    return (
        device_service,
        reading_service,
        aquarium_service,
        aquarium_device_service,
        calibration_repo,
        conn,
    )
