from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import sleep
from uuid import UUID

import pytest

from app.core.exceptions import DomainError
from app.domain.aquarium import Aquarium
from tests.conftest import ServiceBundle

# Test Setup Helper


def make_services(service_bundle: ServiceBundle):
    return service_bundle.device_service, service_bundle.reading_service


async def prepare_device_for_readings(
    service_bundle: ServiceBundle,
    device_id,
    owner_id,
) -> None:
    aquarium = await service_bundle.aquarium_service.create_aquarium(
        Aquarium(
            user_id=owner_id,
            name="Unit Tank",
            water_type="fresh",
            liters=50,
            temperature_min=22,
            temperature_max=26,
            ph_min=6.5,
            ph_max=7.5,
            tds_min=150,
            tds_max=350,
        )
    )
    await service_bundle.calibration_repo.create_point(
        device_id=device_id, ph_point=4.01, voltage=3.0, is_active=True
    )
    await service_bundle.calibration_repo.create_point(
        device_id=device_id, ph_point=6.86, voltage=2.5, is_active=True
    )
    await service_bundle.calibration_repo.create_point(
        device_id=device_id, ph_point=9.18, voltage=2.0, is_active=True
    )
    await service_bundle.aquarium_device_service.attach_device(owner_id, aquarium.id, device_id)


# Sorting Behavior


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_readings_sorted_newest_first(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="Tank", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    r1 = await read_service.create_reading(
        device_id=device.id,
        temperature_c=25,
        raw_ph_voltage=2.0,
        raw_tds_voltage=1.0,
    )
    sleep(0.001)  # force timestamp delta
    r2 = await read_service.create_reading(
        device_id=device.id,
        temperature_c=26,
        raw_ph_voltage=2.1,
        raw_tds_voltage=1.0,
    )

    readings = await read_service.list_readings()

    assert readings[0].received_at >= readings[1].received_at
    assert readings[0] == r2
    assert readings[1] == r1


# Pagination Edge Cases


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_pagination_out_of_range_returns_empty_list(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="X", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    # Insert 5 readings
    for _ in range(5):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=25,
            raw_ph_voltage=2.48,
            raw_tds_voltage=1.0,
        )

    page, total = await read_service.list_readings_paginated(page=10, page_size=10)

    assert total == 5
    assert page == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_pagination_exact_boundary(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="X", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    # Insert exactly 10 readings
    for _ in range(10):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=25,
            raw_ph_voltage=2.0,
            raw_tds_voltage=1.0,
        )

    page, total = await read_service.list_readings_paginated(page=1, page_size=10)

    assert total == 10
    assert len(page) == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_pagination_multiple_pages(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="X", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    # Insert 25 readings
    for _ in range(25):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=25,
            raw_ph_voltage=2.0,
            raw_tds_voltage=1.0,
        )

    p1, _ = await read_service.list_readings_paginated(page=1, page_size=10)
    p2, _ = await read_service.list_readings_paginated(page=2, page_size=10)
    p3, _ = await read_service.list_readings_paginated(page=3, page_size=10)

    assert len(p1) == 10
    assert len(p2) == 10
    assert len(p3) == 5  # remainder


# Latest Reading Behavior


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_get_latest_reading_returns_none_if_no_readings(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="A", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    assert await read_service.get_latest_reading(device.id) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_get_latest_reading_after_many_reads(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="A", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    # First
    await read_service.create_reading(
        device_id=device.id,
        temperature_c=20,
        raw_ph_voltage=2.0,
        raw_tds_voltage=1.0,
    )
    sleep(0.001)
    second = await read_service.create_reading(
        device_id=device.id,
        temperature_c=21,
        raw_ph_voltage=2.1,
        raw_tds_voltage=1.0,
    )

    latest = await read_service.get_latest_reading(device.id)
    assert latest == second


# Domain Validation Bubble-up


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_invalid_reading_values_propagate_error_from_service(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="Bad", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    with pytest.raises(ValueError, match="temperature"):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=200,  # invalid
            raw_ph_voltage=2.0,
            raw_tds_voltage=1.0,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_invalid_tds_voltage_propagates(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="Bad", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    with pytest.raises(ValueError, match="raw_tds_voltage"):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=25,
            raw_ph_voltage=2.0,
            raw_tds_voltage=999,  # impossible
        )


# Multi-device Isolation


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_readings_are_isolated_per_device(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)

    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    dev_a = await dev_service.register_device(name="A", owner_user_id=owner_id)
    dev_b = await dev_service.register_device(name="B", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, dev_a.id, owner_id)
    await prepare_device_for_readings(service_bundle, dev_b.id, owner_id)

    # A gets 3 readings
    for _ in range(3):
        await read_service.create_reading(
            device_id=dev_a.id,
            temperature_c=25,
            raw_ph_voltage=2.0,
            raw_tds_voltage=1.0,
        )

    # B gets 1 reading
    await read_service.create_reading(
        device_id=dev_b.id,
        temperature_c=25,
        raw_ph_voltage=2.0,
        raw_tds_voltage=1.0,
    )

    readings_a = await read_service.list_readings_for_device(dev_a.id)
    readings_b = await read_service.list_readings_for_device(dev_b.id)

    assert len(readings_a) == 3
    assert len(readings_b) == 1
    assert readings_a != readings_b


# Device Stats


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_device_stats_returns_medians(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="Stats", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    await read_service.create_reading(
        device_id=device.id, temperature_c=20, raw_ph_voltage=2.0, raw_tds_voltage=1.0
    )
    await read_service.create_reading(
        device_id=device.id, temperature_c=22, raw_ph_voltage=2.1, raw_tds_voltage=1.0
    )
    await read_service.create_reading(
        device_id=device.id, temperature_c=24, raw_ph_voltage=2.2, raw_tds_voltage=1.0
    )

    stats = await read_service.get_device_stats(device_id=device.id)
    assert stats["temperature_median"] == 22.0
    assert stats["ph_median"] >= 0
    assert stats["tds_median"] >= 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_device_stats_no_readings_raises(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="NoStats", owner_user_id=owner_id)
    await prepare_device_for_readings(service_bundle, device.id, owner_id)

    with pytest.raises(DomainError):
        await read_service.get_device_stats(device_id=device.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_create_reading_requires_attachment(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="Detached", owner_user_id=owner_id)

    with pytest.raises(DomainError, match="attached"):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=25,
            raw_ph_voltage=2.0,
            raw_tds_voltage=1.0,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_create_reading_requires_calibration(service_bundle: ServiceBundle):
    dev_service, read_service = make_services(service_bundle)
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await dev_service.register_device(name="Uncalibrated", owner_user_id=owner_id)

    aquarium = await service_bundle.aquarium_service.create_aquarium(
        Aquarium(
            user_id=owner_id,
            name="Unit Tank",
            water_type="fresh",
            liters=50,
            temperature_min=22,
            temperature_max=26,
            ph_min=6.5,
            ph_max=7.5,
            tds_min=150,
            tds_max=350,
        )
    )
    # Bypass calibration by attaching directly via repo
    await service_bundle.aquarium_device_repo.attach(aquarium.id, device.id)

    with pytest.raises(DomainError, match="calibration"):
        await read_service.create_reading(
            device_id=device.id,
            temperature_c=25,
            raw_ph_voltage=2.0,
            raw_tds_voltage=1.0,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_series_requires_valid_range(service_bundle: ServiceBundle):
    _, read_service = make_services(service_bundle)
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="from must be before to"):
        await read_service.get_series(
            device_id=UUID("00000000-0000-0000-0000-000000000000"),
            from_dt=now,
            to_dt=now - timedelta(hours=1),
            bucket_seconds=60,
        )
