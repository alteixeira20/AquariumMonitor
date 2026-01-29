from __future__ import annotations

from uuid import UUID

import pytest

from app.core.exceptions import DomainError
from app.services.ph_calibration_service import PhCalibrationService
from tests.conftest import ServiceBundle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_calibration_rejects_invalid_ph_point(service_bundle: ServiceBundle):
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await service_bundle.device_service.register_device(
        name="Calib", owner_user_id=owner_id
    )
    service = PhCalibrationService(
        service_bundle.device_service.repository,
        service_bundle.aquarium_service.repository,
        service_bundle.aquarium_device_service.association_repo,
        service_bundle.reading_service.reading_repo,
        service_bundle.calibration_repo,
    )

    with pytest.raises(DomainError, match="Invalid pH point"):
        await service.add_point(owner_id, device.id, 7.0, 2.5)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_calibration_rejects_invalid_voltage(service_bundle: ServiceBundle):
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await service_bundle.device_service.register_device(
        name="Calib", owner_user_id=owner_id
    )
    service = PhCalibrationService(
        service_bundle.device_service.repository,
        service_bundle.aquarium_service.repository,
        service_bundle.aquarium_device_service.association_repo,
        service_bundle.reading_service.reading_repo,
        service_bundle.calibration_repo,
    )

    with pytest.raises(DomainError, match="Invalid voltage"):
        await service.add_point(owner_id, device.id, 4.01, 99.0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_activate_requires_all_points(service_bundle: ServiceBundle):
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    device = await service_bundle.device_service.register_device(
        name="Calib", owner_user_id=owner_id
    )
    service = PhCalibrationService(
        service_bundle.device_service.repository,
        service_bundle.aquarium_service.repository,
        service_bundle.aquarium_device_service.association_repo,
        service_bundle.reading_service.reading_repo,
        service_bundle.calibration_repo,
    )

    await service.add_point(owner_id, device.id, 4.01, 3.0)

    with pytest.raises(DomainError, match="Calibration requires"):
        await service.activate(owner_id, device.id)
