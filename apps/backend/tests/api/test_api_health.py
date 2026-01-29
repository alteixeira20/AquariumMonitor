from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/v1/health")
    assert res.status_code == 200

    data = res.json()
    assert data.get("status") == "ok"
    assert "timestamp" in data


def test_readiness_endpoint():
    res = client.get("/v1/readiness")
    assert res.status_code == 200

    data = res.json()
    assert data.get("status") == "ready"
    assert data.get("environment") is not None
    assert "db_status" in data
    assert "storage_backend" in data


def test_metrics_endpoint():
    res = client.get("/v1/metrics")
    assert res.status_code == 200

    data = res.json()
    assert "devices_count" in data
    assert "readings_count" in data
    assert data["devices_count"] >= 0
    assert data["readings_count"] >= 0


def test_prometheus_metrics_endpoint():
    res = client.get("/v1/metrics/prometheus")
    assert res.status_code == 200
    assert "app_requests_total" in res.text
