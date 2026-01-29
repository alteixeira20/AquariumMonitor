from __future__ import annotations

from datetime import UTC, datetime
import logging
from pathlib import Path
from typing import Any

import aiosqlite
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.core.metrics import render_prometheus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service health check",
)
def health_check() -> dict[str, str]:
    """Basic liveness endpoint."""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="Service readiness check",
)
async def readiness_check(request: Request) -> dict[str, Any]:
    """Readiness endpoint with environment info and optional DB probe."""
    settings = get_settings()
    db_status = "not_checked"
    db_path = getattr(request.app.state, "db_path", None)
    required_tables = _required_tables(settings.storage_backend)
    healthy = True

    if settings.storage_backend == "sqlite":
        db_conn = getattr(request.app.state, "db_conn", None)
        db_status, healthy = await _check_sqlite(db_conn, required_tables)
        if db_path and not Path(db_path).exists():
            logger.error("SQLite database file missing at %s", db_path)
            db_status = "missing_file"
            healthy = False
    elif settings.storage_backend == "mariadb":
        db_engine = getattr(request.app.state, "db_engine", None)
        db_status, healthy = await _check_mariadb(db_engine, settings.db_name, required_tables)

    response_body = {
        "status": "ready",
        "environment": settings.environment,
        "storage_backend": settings.storage_backend,
        "db_status": db_status,
    }

    if healthy:
        return response_body

    # Surface degraded state with 503 to make failures visible to orchestrators
    return JSONResponse(response_body, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Lightweight metrics snapshot",
)
async def metrics(request: Request) -> dict[str, Any]:
    """Return simple counters for devices and readings."""
    device_service = request.app.state.device_service
    reading_service = request.app.state.reading_service

    devices = await device_service.list_devices()
    readings = await reading_service.list_readings()

    return {
        "devices_count": len(devices),
        "readings_count": len(readings),
    }


@router.get(
    "/metrics/prometheus",
    status_code=status.HTTP_200_OK,
    summary="Prometheus metrics",
)
async def metrics_prometheus() -> PlainTextResponse:
    payload = render_prometheus()
    return PlainTextResponse(payload, media_type="text/plain; version=0.0.4")


def _required_tables(storage_backend: str) -> tuple[str, ...]:
    if storage_backend == "sqlite":
        return (
            "users",
            "aquariums",
            "devices",
            "readings",
            "aquarium_devices",
            "device_api_keys",
            "device_ph_calibrations",
        )
    return (
        "users",
        "aquariums",
        "devices",
        "readings",
        "aquarium_devices",
        "device_api_keys",
        "device_ph_calibrations",
    )


async def _check_sqlite(
    db_conn: object, required_tables: tuple[str, ...]
) -> tuple[str, bool]:
    if not isinstance(db_conn, aiosqlite.Connection):
        return "not_checked", True
    try:
        await db_conn.execute("SELECT 1;")
        missing_tables = await _sqlite_missing_tables(db_conn, required_tables)
        if missing_tables:
            return f"schema_missing:{','.join(missing_tables)}", False
        return "ok", True
    except Exception as exc:  # pragma: no cover - defensive
        return f"error:{exc.__class__.__name__}", False


async def _sqlite_missing_tables(
    db_conn: aiosqlite.Connection, required_tables: tuple[str, ...]
) -> list[str]:
    missing_tables: list[str] = []
    for table in required_tables:
        cursor = await db_conn.execute(f"PRAGMA table_info({table});")
        rows = await cursor.fetchall()
        await cursor.close()
        if not rows:
            missing_tables.append(table)
    return missing_tables


async def _check_mariadb(
    db_engine: object, schema: str, required_tables: tuple[str, ...]
) -> tuple[str, bool]:
    if not isinstance(db_engine, AsyncEngine):
        return "not_checked", True
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            query = text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema AND table_name IN :table_list
                """
            ).bindparams(bindparam("table_list", expanding=True))
            result = await conn.execute(
                query, {"schema": schema, "table_list": list(required_tables)}
            )
            found = {row[0] for row in result.fetchall()}
            missing = sorted(set(required_tables) - found)
            if missing:
                return f"schema_missing:{','.join(missing)}", False
            return "ok", True
    except Exception as exc:  # pragma: no cover - defensive
        return f"error:{exc.__class__.__name__}", False
