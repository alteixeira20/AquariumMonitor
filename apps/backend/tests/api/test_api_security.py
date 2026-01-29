from __future__ import annotations

import os
from contextlib import contextmanager
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.jwt_utils import create_jwt
from app.main import create_app


@contextmanager
def _temp_env(values: dict[str, str]):
    old = os.environ.copy()
    os.environ.update(values)
    get_settings.cache_clear()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)
        get_settings.cache_clear()


def _build_client(env: dict[str, str]) -> TestClient:
    get_settings.cache_clear()
    with _temp_env(env):
        app = create_app()
        return TestClient(app, raise_server_exceptions=False)


def _owner_token(owner_id: UUID) -> str:
    return create_jwt({"sub": str(owner_id), "email": "owner@example.com", "role": "owner"})


def _prepare_device_flow(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    device = client.post("/v1/devices", json={"name": "Sensor"}, headers=headers).json()
    aquarium = client.post(
        "/v1/aquariums",
        json={
            "name": "Tank",
            "water_type": "fresh",
            "liters": 50,
            "temperature_min": 22,
            "temperature_max": 26,
            "ph_min": 6.5,
            "ph_max": 7.5,
            "tds_min": 150,
            "tds_max": 350,
        },
        headers=headers,
    ).json()
    device_id = device["id"]
    aquarium_id = aquarium["id"]
    for ph_point, voltage in [(4.01, 3.0), (6.86, 2.5), (9.18, 2.0)]:
        client.post(
            f"/v1/devices/{device_id}/calibration/points",
            json={"ph_point": ph_point, "voltage": voltage},
            headers=headers,
        )
    client.post(f"/v1/devices/{device_id}/calibration/activate", headers=headers)
    client.post(f"/v1/aquariums/{aquarium_id}/devices/{device_id}", headers=headers)
    key_res = client.post(f"/v1/devices/{device_id}/api-keys", headers=headers)
    return device_id, key_res.json()["api_key"]


def test_rate_limit_blocks_after_threshold():
    with _temp_env(
        {
            "STORAGE_BACKEND": "memory",
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_REQUESTS": "1",
            "RATE_LIMIT_WINDOW_SECONDS": "60",
        }
    ):
        get_settings.cache_clear()
        client = TestClient(create_app(), raise_server_exceptions=False)
        first = client.get("/v1/events")
        second = client.get("/v1/events")

    assert first.status_code == 200
    assert second.status_code == 429


def test_single_owner_mode_blocks_non_owner():
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    other_id = UUID("00000000-0000-0000-0000-000000000001")
    with _temp_env(
        {
            "STORAGE_BACKEND": "memory",
            "SINGLE_OWNER_MODE": "true",
            "OWNER_USER_ID": str(owner_id),
        }
    ):
        get_settings.cache_clear()
        client = TestClient(create_app(), raise_server_exceptions=False)
        bad_headers = {"Authorization": f"Bearer {create_jwt({'sub': str(other_id)})}"}
        res = client.get("/v1/aquariums", headers=bad_headers)
        assert res.status_code == 403

        ok_headers = {"Authorization": f"Bearer {create_jwt({'sub': str(owner_id)})}"}
        res_ok = client.get("/v1/aquariums", headers=ok_headers)
        assert res_ok.status_code == 200


def test_device_api_key_invalid_and_revoked():
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    client = _build_client({"STORAGE_BACKEND": "memory"})
    headers = {"Authorization": f"Bearer {_owner_token(owner_id)}"}

    device_id, api_key = _prepare_device_flow(client, headers)

    invalid_res = client.post(
        f"/v1/readings/{device_id}",
        headers={"Authorization": "Bearer invalid"},
        json={"temperature_c": 25, "raw_ph_voltage": 2.0, "raw_tds_voltage": 1.0},
    )
    assert invalid_res.status_code == 401

    revoke_res = client.post(
        f"/v1/devices/{device_id}/api-keys/revoke",
        headers=headers,
        json={"api_key": api_key},
    )
    assert revoke_res.status_code == 204

    revoked = client.post(
        f"/v1/readings/{device_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"temperature_c": 25, "raw_ph_voltage": 2.0, "raw_tds_voltage": 1.0},
    )
    assert revoked.status_code == 401
