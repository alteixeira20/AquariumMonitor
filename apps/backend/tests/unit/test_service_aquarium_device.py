from __future__ import annotations

from uuid import UUID

import pytest

from app.core.exceptions import DomainError
from app.domain.aquarium import Aquarium
from tests.conftest import ServiceBundle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_attach_requires_calibration(service_bundle: ServiceBundle):
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
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
    device = await service_bundle.device_service.register_device(
        name="NoCalibration", owner_user_id=owner_id
    )

    with pytest.raises(DomainError, match="calibration"):
        await service_bundle.aquarium_device_service.attach_device(
            owner_id, aquarium.id, device.id
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_attach_requires_device_owner(service_bundle: ServiceBundle):
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    other_id = UUID("00000000-0000-0000-0000-000000000001")
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
    device = await service_bundle.device_service.register_device(
        name="OtherOwner", owner_user_id=other_id
    )

    with pytest.raises(DomainError, match="not owned"):
        await service_bundle.aquarium_device_service.attach_device(
            owner_id, aquarium.id, device.id
        )
