from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import aiosqlite
import pytest

from app.domain.reading import Reading
from app.repositories.sqlite_repository import (
    SqliteDeviceRepository,
    SqliteReadingRepository,
    init_db,
)


@pytest.fixture
async def sqlite_repos(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = await aiosqlite.connect(db_path)
    await init_db(db_path, conn)

    device_repo = SqliteDeviceRepository(conn)
    reading_repo = SqliteReadingRepository(conn)

    yield device_repo, reading_repo

    await conn.close()


@pytest.mark.asyncio
async def test_device_repo_create_and_get(
    sqlite_repos: tuple[SqliteDeviceRepository, SqliteReadingRepository],
):
    device_repo, _ = sqlite_repos

    created = await device_repo.create(name="Tank", location="Lab", owner_user_id=None)
    fetched = await device_repo.get(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Tank"


@pytest.mark.asyncio
async def test_device_repo_list_for_owner(
    sqlite_repos: tuple[SqliteDeviceRepository, SqliteReadingRepository],
):
    device_repo, _ = sqlite_repos
    owner_id = UUID("00000000-0000-0000-0000-000000000000")

    await device_repo.create(name="Owned-1", location=None, owner_user_id=owner_id)
    await device_repo.create(name="Owned-2", location=None, owner_user_id=owner_id)
    await device_repo.create(name="Other", location=None, owner_user_id=None)

    owned = await device_repo.list_for_owner(owner_id)
    names = {d.name for d in owned}
    assert "Owned-1" in names
    assert "Owned-2" in names
    assert "Other" not in names


@pytest.mark.asyncio
async def test_reading_repo_create_and_list(
    sqlite_repos: tuple[SqliteDeviceRepository, SqliteReadingRepository],
):
    device_repo, reading_repo = sqlite_repos

    device = await device_repo.create(name="R1", location=None, owner_user_id=None)

    reading = Reading(
        device_id=device.id,
        temperature_c=25.0,
        raw_ph_voltage=2.48,
        raw_tds_voltage=1.0,
        received_at=datetime.now(UTC),
    )
    reading.process()

    await reading_repo.create(reading)

    readings = await reading_repo.list_for_device(device.id)
    assert len(readings) == 1
    assert readings[0].device_id == device.id
    assert readings[0].ph_value is not None
    assert readings[0].tds_ppm is not None


@pytest.mark.asyncio
async def test_reading_repo_latest_and_pagination(
    sqlite_repos: tuple[SqliteDeviceRepository, SqliteReadingRepository],
):
    device_repo, reading_repo = sqlite_repos
    device = await device_repo.create(name="Paginated", location=None, owner_user_id=None)

    base_time = datetime.now(UTC)
    for i in range(5):
        reading = Reading(
            device_id=device.id,
            temperature_c=25 + i,
            raw_ph_voltage=2.0 + i * 0.01,
            raw_tds_voltage=1.0,
            received_at=base_time + timedelta(seconds=i),
        )
        reading.process()
        await reading_repo.create(reading)

    latest = await reading_repo.get_latest(device.id)
    assert latest is not None
    assert latest.temperature_c == 25 + 4

    page1, total = await reading_repo.list_for_device_paginated(
        device_id=device.id, page=1, page_size=3
    )
    page2, _ = await reading_repo.list_for_device_paginated(
        device_id=device.id, page=2, page_size=3
    )

    assert total == 5
    assert len(page1) == 3
    assert len(page2) == 2
