from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# Helper to create device first
def create_device(name: str = "Tank") -> str:
    res = client.post("/v1/devices", json={"name": name})
    assert res.status_code == 201
    return res.json()["id"]


def prepare_device_for_readings(device_id: str) -> None:
    aquarium_res = client.post(
        "/v1/aquariums",
        json={
            "name": "Test Tank",
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


def test_create_reading_api():
    device_id = create_device()
    prepare_device_for_readings(device_id)

    payload = {
        "temperature_c": 25,
        "raw_ph_voltage": 2.48,
        "raw_tds_voltage": 1.2,
    }

    res = client.post(f"/v1/readings/{device_id}", json=payload)
    assert res.status_code == 201

    data = res.json()

    assert "ph_value" in data
    assert "tds_ppm" in data
    assert data["device_id"] == device_id


def test_create_reading_invalid_payload():
    device_id = create_device()
    prepare_device_for_readings(device_id)

    payload = {
        "temperature_c": 999,  # invalid temperature
        "raw_ph_voltage": 1,
        "raw_tds_voltage": 1,
    }

    res = client.post(f"/v1/readings/{device_id}", json=payload)
    assert res.status_code in (400, 422)


def test_list_readings_api():
    device_id = create_device()
    prepare_device_for_readings(device_id)

    # Create some readings
    for v in [2.0, 2.2, 2.3]:
        client.post(
            f"/v1/readings/{device_id}",
            json={"temperature_c": 25, "raw_ph_voltage": v, "raw_tds_voltage": 1.0},
        )

    res = client.get(f"/v1/readings/{device_id}")
    assert res.status_code == 200

    items = res.json()
    assert isinstance(items, list)
    assert len(items) >= 3


def test_list_readings_empty_for_new_device():
    device_id = create_device(name="NoReadingsYet")
    prepare_device_for_readings(device_id)

    res = client.get(f"/v1/readings/{device_id}")
    assert res.status_code == 200
    assert res.json() == []


def test_latest_reading_api():
    device_id = create_device()
    prepare_device_for_readings(device_id)

    client.post(
        f"/v1/readings/{device_id}",
        json={"temperature_c": 25, "raw_ph_voltage": 2.0, "raw_tds_voltage": 1.0},
    )

    res = client.get(f"/v1/readings/{device_id}/latest")
    assert res.status_code == 200

    data = res.json()
    assert UUID(data["device_id"]) == UUID(device_id)


def test_latest_reading_no_data_returns_404():
    device_id = create_device(name="EmptyDevice")
    prepare_device_for_readings(device_id)

    res = client.get(f"/v1/readings/{device_id}/latest")
    assert res.status_code == 404


def test_paginated_query_validation():
    device_id = create_device(name="Paged")
    prepare_device_for_readings(device_id)

    res = client.get(f"/v1/readings/{device_id}/paginated", params={"page": 0})
    assert res.status_code == 422


def test_series_endpoint():
    device_id = create_device(name="Series")
    prepare_device_for_readings(device_id)

    client.post(
        f"/v1/readings/{device_id}",
        json={"temperature_c": 25, "raw_ph_voltage": 2.0, "raw_tds_voltage": 1.0},
    )

    res = client.get(
        f"/v1/readings/{device_id}/series",
        params={"bucket_seconds": 60},
    )
    assert res.status_code == 200
    data = res.json()
    assert "bucket_seconds" in data
    assert "points" in data
