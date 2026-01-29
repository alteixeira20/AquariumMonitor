from __future__ import annotations

import pytest

from tests.conftest import ServiceBundle, seed_sample_data


@pytest.mark.db_seed_only
@pytest.mark.sqlite_only
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_bundle",
    [pytest.param("sqlite", marks=pytest.mark.sqlite_only)],
    indirect=True,
)
async def test_seed_database(service_bundle: ServiceBundle):
    """
    Seeds the database with sample data for inspection after test-sqlite runs.
    """
    await seed_sample_data(
        service_bundle.device_service,
        service_bundle.reading_service,
        service_bundle.aquarium_service,
        service_bundle.aquarium_device_service,
        service_bundle.calibration_repo,
    )
