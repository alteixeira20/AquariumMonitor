from __future__ import annotations

from uuid import UUID

import pytest

from app.domain.device import Device
from app.core.exceptions import DomainError
from tests.conftest import ServiceBundle


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_register_device(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    d = await service.register_device(name="Tank1", location="Office")

    assert isinstance(d, Device)
    assert d.name == "Tank1"
    assert d.location == "Office"
    assert isinstance(d.id, UUID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_get_device_success(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    created = await service.register_device(name="A")

    found = await service.get_device(created.id)
    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_get_device_not_found(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    missing = await service.get_device(UUID(int=123))

    assert missing is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_list_devices(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    await service.register_device(name="A")
    await service.register_device(name="B")

    all_devices = await service.list_devices()
    assert len(all_devices) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_device_update_methods_reflect_in_service(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    d = await service.register_device(name="X", location="Lab")

    await service.update_device_name(d.id, "Updated")
    await service.update_device_location(d.id, "Kitchen")
    await service.deactivate_device(d.id)

    saved = await service.get_device(d.id)

    assert saved is not None
    assert saved.name == "Updated"
    assert saved.location == "Kitchen"
    assert saved.is_active is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_claim_device_conflict(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    owner_a = UUID("00000000-0000-0000-0000-000000000000")
    owner_b = UUID("00000000-0000-0000-0000-000000000001")
    device = await service.register_device(name="Claimed", owner_user_id=owner_a)

    with pytest.raises(DomainError):
        await service.claim_device(device.id, owner_b)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    ["memory", pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_claim_device_idempotent_for_same_owner(service_bundle: ServiceBundle):
    service = service_bundle.device_service
    owner = UUID("00000000-0000-0000-0000-000000000000")
    device = await service.register_device(name="Claimed", owner_user_id=owner)

    claimed = await service.claim_device(device.id, owner)
    assert claimed.owner_user_id == owner
