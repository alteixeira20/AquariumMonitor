from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def _client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(create_app(), raise_server_exceptions=False)


def _ensure_owner_setup() -> None:
    client = _client()
    status = client.get("/v1/setup/status")
    assert status.status_code == 200
    if status.json().get("configured"):
        return
    res = client.post(
        "/v1/setup",
        json={"email": "owner@example.com", "password": "change-me-please"},
    )
    assert res.status_code == 201


def test_setup_and_login_flow():
    client = _client()
    status = client.get("/v1/setup/status")
    assert status.status_code == 200
    configured = status.json().get("configured")

    if not configured:
        setup = client.post(
            "/v1/setup",
            json={"email": "owner@example.com", "password": "change-me-please"},
        )
        assert setup.status_code == 201

    login = client.post(
        "/v1/login",
        json={"email": "owner@example.com", "password": "change-me-please"},
    )
    assert login.status_code == 200
    payload = login.json()
    assert "access_token" in payload

    status_after = client.get("/v1/setup/status")
    assert status_after.status_code == 200
    assert status_after.json().get("configured") is True


def test_demo_login_is_read_only():
    client = _client()
    status = client.get("/v1/setup/status")
    assert status.status_code == 200
    if not status.json().get("configured"):
        setup = client.post(
            "/v1/setup",
            json={"email": "owner@example.com", "password": "change-me-please"},
        )
        assert setup.status_code == 201
    settings = get_settings()
    if not settings.demo_enabled:
        pytest.skip("Demo login disabled in settings")

    demo_login = client.post(
        "/v1/login",
        json={"email": settings.demo_username, "password": settings.demo_password},
    )
    assert demo_login.status_code == 200
    token = demo_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Read-only access should allow GETs
    list_res = client.get("/v1/aquariums", headers=headers)
    assert list_res.status_code == 200

    # Writes should be blocked
    create_res = client.post(
        "/v1/aquariums",
        headers=headers,
        json={
            "name": "Demo Tank",
            "water_type": "fresh",
            "liters": 50,
            "temperature_min": 22,
            "temperature_max": 26,
            "ph_min": 6.5,
            "ph_max": 7.5,
            "tds_min": 150,
            "tds_max": 350,
        },
    )
    assert create_res.status_code == 403
