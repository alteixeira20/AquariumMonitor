from __future__ import annotations

import logging

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def test_validation_error_shape():
    res = client.post("/v1/devices", json={"name": 123})
    assert res.status_code == 422

    data = res.json()
    assert data["error"] == "validation_error"
    assert "message" in data
    assert isinstance(data.get("details"), list)


def test_http_exception_shape_not_found():
    res = client.get("/v1/devices/00000000-0000-0000-0000-000000000001")
    assert res.status_code == 404

    data = res.json()
    assert data["error"] == "not_found"
    assert "message" in data


def test_request_logging_middleware(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="app.requests")

    res = client.get("/v1/health")
    assert res.status_code == 200

    records = [r for r in caplog.records if r.name == "app.requests"]
    assert any("request" in r.msg for r in records)
