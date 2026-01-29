from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_device_api():
    payload = {"name": "Tank1", "location": "Office"}
    res = client.post("/v1/devices", json=payload)

    assert res.status_code == 201
    data = res.json()

    assert data["name"] == "Tank1"
    assert data["location"] == "Office"
    assert UUID(data["id"])  # valid UUID


def test_register_device_validation_error():
    # Wrong types
    payload = {"name": 123, "location": True}
    res = client.post("/v1/devices", json=payload)

    assert res.status_code == 422  # Pydantic validation error


def test_get_device_success():
    # First create
    res = client.post("/v1/devices", json={"name": "A"})
    device_id = res.json()["id"]

    # Then fetch
    get_res = client.get(f"/v1/devices/{device_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == device_id


def test_get_device_not_found():
    res = client.get("/v1/devices/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_get_device_invalid_uuid():
    res = client.get("/v1/devices/not-a-uuid")
    assert res.status_code == 422


def test_list_devices():
    client.post("/v1/devices", json={"name": "A"})
    client.post("/v1/devices", json={"name": "B"})

    res = client.get("/v1/devices")
    assert res.status_code == 200

    items = res.json()
    assert isinstance(items, list)
    assert len(items) >= 2


def test_list_owned_devices():
    res = client.post("/v1/devices", json={"name": "Owned"})
    device_id = res.json()["id"]

    owned_res = client.get("/v1/devices/owned")
    assert owned_res.status_code == 200
    ids = [item["id"] for item in owned_res.json()]
    assert device_id in ids


def prepare_device_for_readings(device_id: str) -> None:
    aquarium_res = client.post(
        "/v1/aquariums",
        json={
            "name": "Stats Tank",
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
    assert aquarium_res.status_code == 201
    aquarium_id = aquarium_res.json()["id"]

    for ph_point, voltage in [(4.01, 3.0), (6.86, 2.5), (9.18, 2.0)]:
        point_res = client.post(
            f"/v1/devices/{device_id}/calibration/points",
            json={"ph_point": ph_point, "voltage": voltage},
        )
        assert point_res.status_code == 201

    activate_res = client.post(f"/v1/devices/{device_id}/calibration/activate")
    assert activate_res.status_code == 200

    attach_res = client.post(f"/v1/aquariums/{aquarium_id}/devices/{device_id}")
    assert attach_res.status_code == 204


def test_device_stats():
    res = client.post("/v1/devices", json={"name": "Stats"})
    device_id = res.json()["id"]
    prepare_device_for_readings(device_id)

    client.post(
        f"/v1/readings/{device_id}",
        json={"temperature_c": 20, "raw_ph_voltage": 2.0, "raw_tds_voltage": 1.0},
    )
    client.post(
        f"/v1/readings/{device_id}",
        json={"temperature_c": 22, "raw_ph_voltage": 2.1, "raw_tds_voltage": 1.0},
    )

    stats_res = client.get(f"/v1/devices/{device_id}/stats")
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert "temperature_median" in data
    assert "ph_median" in data
    assert "tds_median" in data


def test_device_api_key_revoke():
    res = client.post("/v1/devices", json={"name": "KeyDevice"})
    device_id = res.json()["id"]

    key_res = client.post(f"/v1/devices/{device_id}/api-keys")
    assert key_res.status_code == 201
    api_key = key_res.json()["api_key"]

    revoke_res = client.post(
        f"/v1/devices/{device_id}/api-keys/revoke", json={"api_key": api_key}
    )
    assert revoke_res.status_code == 204
