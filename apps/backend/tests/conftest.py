from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import inspect
import os
from pathlib import Path
from uuid import UUID

import aiosqlite
from fastapi import Request
import pytest

from app.api.v1.devices import get_aquarium_device_service as devices_aquarium_device_service
from app.api.v1.readings import get_aquarium_device_service as readings_aquarium_device_service
from app.core.auth import device_api_key_dependency, jwt_dependency
from app.core.security import hash_password
from app.domain.aquarium import Aquarium
from app.main import app
from app.repositories.memory_repository import (
    MemoryAquariumDeviceRepository,
    MemoryAquariumRepository,
    MemoryDeviceRepository,
    MemoryPhCalibrationRepository,
    MemoryReadingRepository,
)
from app.repositories.base_repository import AquariumDeviceRepository, PhCalibrationRepository
from app.repositories.sqlite_repository import (
    SqliteAquariumDeviceRepository,
    SqliteAquariumRepository,
    SqliteDeviceRepository,
    SqlitePhCalibrationRepository,
    SqliteReadingRepository,
    init_db,
)
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.aquarium_service import AquariumService
from app.services.device_service import DeviceService
from app.services.reading_service import ReadingService


@dataclass
class ServiceBundle:
    device_service: DeviceService
    reading_service: ReadingService
    aquarium_service: AquariumService
    aquarium_device_service: AquariumDeviceService
    calibration_repo: PhCalibrationRepository
    aquarium_device_repo: AquariumDeviceRepository


async def seed_sample_data(
    device_service: DeviceService,
    reading_service: ReadingService,
    aquarium_service: AquariumService,
    aquarium_device_service: AquariumDeviceService,
    calibration_repo: PhCalibrationRepository,
) -> None:
    """
    Populate the repository with sample devices and readings for inspection.
    Uses both valid and invalid attempts (invalid ones are ignored).

    After this runs you should see:
    - 3 devices (Alpha, Beta, Gamma)
    - Alpha with 6 readings
    - Beta with 3 readings
    - Gamma with 1 reading (and one invalid attempt ignored)
    """
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    aquarium = await aquarium_service.create_aquarium(
        Aquarium(
            user_id=owner_id,
            name="Seed Tank",
            water_type="fresh",
            liters=100,
            temperature_min=22,
            temperature_max=26,
            ph_min=6.5,
            ph_max=7.5,
            tds_min=150,
            tds_max=350,
        )
    )

    dev1 = await device_service.register_device(
        name="Seed-Alpha", location="Lab", owner_user_id=owner_id
    )
    dev2 = await device_service.register_device(
        name="Seed-Beta", location="Field", owner_user_id=owner_id
    )
    dev3 = await device_service.register_device(
        name="Seed-Gamma", location="Warehouse", owner_user_id=owner_id
    )

    for device in (dev1, dev2, dev3):
        await calibration_repo.create_point(
            device_id=device.id, ph_point=4.01, voltage=3.0, is_active=True
        )
        await calibration_repo.create_point(
            device_id=device.id, ph_point=6.86, voltage=2.5, is_active=True
        )
        await calibration_repo.create_point(
            device_id=device.id, ph_point=9.18, voltage=2.0, is_active=True
        )
        await aquarium_device_service.attach_device(owner_id, aquarium.id, device.id)

    # Valid readings for Alpha (6)
    for volts in [2.0, 2.1, 2.2, 2.3, 2.4, 2.5]:
        await reading_service.create_reading(
            device_id=dev1.id,
            temperature_c=25,
            raw_ph_voltage=volts,
            raw_tds_voltage=1.0,
        )

    # Beta with fewer readings (3)
    await reading_service.create_reading(
        device_id=dev2.id,
        temperature_c=20,
        raw_ph_voltage=2.1,
        raw_tds_voltage=0.9,
    )
    await reading_service.create_reading(
        device_id=dev2.id,
        temperature_c=21,
        raw_ph_voltage=2.05,
        raw_tds_voltage=0.95,
    )
    await reading_service.create_reading(
        device_id=dev2.id,
        temperature_c=19,
        raw_ph_voltage=2.2,
        raw_tds_voltage=1.05,
    )

    # Gamma single reading
    await reading_service.create_reading(
        device_id=dev3.id,
        temperature_c=22,
        raw_ph_voltage=2.15,
        raw_tds_voltage=1.1,
    )

    # Invalid attempt (caught) to demonstrate validation
    try:
        await reading_service.create_reading(
            device_id=dev2.id,
            temperature_c=999,
            raw_ph_voltage=1.0,
            raw_tds_voltage=1.0,
        )
    except ValueError:
        pass


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests at session scope."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _describe_item(item: pytest.Item) -> str:
    doc = inspect.getdoc(getattr(item, "obj", None))
    if doc:
        return doc.splitlines()[0].strip()
    return item.name.replace("_", " ")


def _group_label(item: pytest.Item) -> str:
    parts = Path(str(item.path)).parts
    if "api" in parts:
        return "API"
    if "unit" in parts:
        return "Unit"
    if "repositories" in parts:
        return "Repository"
    if "integration" in parts:
        return "Integration"
    if "db_seed" in parts:
        return "Seed"
    return "Tests"


def _log_path() -> Path:
    return Path(__file__).resolve().parents[1] / "logs" / "test.log"

_ITEM_DESCRIPTIONS: dict[str, str] = {}
_ITEM_GROUPS: dict[str, str] = {}
_FAILURES: dict[str, str] = {}
_CURRENT_GROUP: str | None = None
_LOG_ENTRIES: list[str] = []


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    config._summary_items = items  # type: ignore[attr-defined]
    _ITEM_DESCRIPTIONS.clear()
    _ITEM_GROUPS.clear()
    for item in items:
        group = _group_label(item)
        _ITEM_GROUPS[item.nodeid] = group
        _ITEM_DESCRIPTIONS[item.nodeid] = _describe_item(item)


def pytest_report_teststatus(
    report: pytest.TestReport, config: pytest.Config
) -> tuple[str, str, str] | None:
    return "", "", ""


def pytest_sessionstart(session: pytest.Session) -> None:
    _write_line(_style("Running tests", "bold"))
    _write_line("=" * 72)
    _LOG_ENTRIES.clear()
    _LOG_ENTRIES.append("Test Log")
    _LOG_ENTRIES.append("")


def _style(text: str, style: str) -> str:
    styles = {
        "bold": "\033[1m",
        "green": "\033[32m",
        "red": "\033[31m",
        "yellow": "\033[33m",
        "reset": "\033[0m",
    }
    return f"{styles.get(style, '')}{text}{styles['reset']}"


def _write_line(message: str) -> None:
    print(message)


def _write_group_header(group: str) -> None:
    _write_line("-" * 72)
    _write_line(_style(f"{group} Testing", "bold"))


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when != "call" and not report.failed:
        return
    global _CURRENT_GROUP
    group = _ITEM_GROUPS.get(report.nodeid, "Tests")
    if group != _CURRENT_GROUP:
        _CURRENT_GROUP = group
        _write_group_header(group)
    description = _ITEM_DESCRIPTIONS.get(report.nodeid, report.nodeid)
    status = "PASSED"
    if report.failed:
        status = "FAILED"
        _FAILURES[report.nodeid] = str(report.longrepr)
    elif report.skipped:
        status = "SKIPPED"
    line = f"\t{description} ... "
    if status == "PASSED":
        colored = _style(status, "green")
    elif status == "FAILED":
        colored = _style(status, "red")
    else:
        colored = _style(status, "yellow")
    _write_line(f"{line}{colored}")
    _LOG_ENTRIES.append(f"{description} ... {status}")
    if status == "FAILED":
        _LOG_ENTRIES.append("  Failure:")
        _LOG_ENTRIES.extend([f"  {line}" for line in _FAILURES[report.nodeid].splitlines()])


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter | None, exitstatus: int, config: pytest.Config
) -> None:
    items: list[pytest.Item] = getattr(config, "_summary_items", [])
    if not items:
        return
    log_path = _log_path()
    current_group = None
    current_file = None
    for item in items:
        group = _ITEM_GROUPS.get(item.nodeid, "Tests")
        if group != current_group:
            current_group = group
            summary_lines.append(f"{group} Testing")
        file_path = str(item.path)
        if file_path != current_file:
            current_file = file_path
            summary_lines.append(f"{file_path}")
        description = _ITEM_DESCRIPTIONS.get(item.nodeid, item.name)
        summary_lines.append(f"- {item.name}: {description}")
        failure = _FAILURES.get(item.nodeid)
        if failure:
            summary_lines.append("  Failure:")
            summary_lines.extend([f"  {line}" for line in failure.splitlines()])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(_LOG_ENTRIES) + "\n", encoding="utf-8")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    log_path = _log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(_LOG_ENTRIES) + "\n", encoding="utf-8")
    terminalreporter = session.config.pluginmanager.getplugin("terminalreporter")
    if terminalreporter:
        terminalreporter.write_line(f"Log written to {log_path}")
    else:
        _write_line(f"Log written to {log_path}")


@pytest.fixture(params=["memory", "sqlite"])
async def service_bundle(
    request: pytest.FixtureRequest, tmp_path: Path
) -> AsyncIterator[ServiceBundle]:
    backend = request.param

    if backend == "memory":
        device_repo = MemoryDeviceRepository()
        reading_repo = MemoryReadingRepository()
        calibration_repo = MemoryPhCalibrationRepository()
        aquarium_repo = MemoryAquariumRepository()
        aquarium_device_repo = MemoryAquariumDeviceRepository()
        yield ServiceBundle(
            device_service=DeviceService(device_repo),
            reading_service=ReadingService(
                device_repo, reading_repo, calibration_repo, aquarium_device_repo
            ),
            aquarium_service=AquariumService(aquarium_repo),
            aquarium_device_service=AquariumDeviceService(
                aquarium_repo, device_repo, aquarium_device_repo, calibration_repo
            ),
            calibration_repo=calibration_repo,
            aquarium_device_repo=aquarium_device_repo,
        )
        return

    if backend == "sqlite":
        env_db_url = os.environ.get("DATABASE_URL")
        use_env_db = bool(request.node.get_closest_marker("db_seed_only"))
        if use_env_db and env_db_url and env_db_url.startswith("sqlite:///"):
            db_path_str = env_db_url.replace("sqlite:///", "", 1)
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            db_path = tmp_path / "test.db"

        conn = await aiosqlite.connect(db_path)
        await init_db(db_path, conn)
        # Ensure a default owner exists for FK constraints.
        await conn.execute(
            """
            INSERT OR IGNORE INTO users (id, email, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "00000000-0000-0000-0000-000000000000",
                "test-owner@example.com",
                hash_password("password"),
                1,
                datetime.utcnow().isoformat(),
            ),
        )
        # Ensure a clean slate per test (preserve users)
        await conn.execute("DELETE FROM readings;")
        await conn.execute("DELETE FROM device_ph_calibrations;")
        await conn.execute("DELETE FROM device_api_keys;")
        await conn.execute("DELETE FROM aquarium_devices;")
        await conn.execute("DELETE FROM devices;")
        await conn.execute("DELETE FROM aquariums;")
        await conn.commit()
        device_repo = SqliteDeviceRepository(conn)
        reading_repo = SqliteReadingRepository(conn)
        calibration_repo = SqlitePhCalibrationRepository(conn)
        aquarium_repo = SqliteAquariumRepository(conn)
        aquarium_device_repo = SqliteAquariumDeviceRepository(conn)
        yield ServiceBundle(
            device_service=DeviceService(device_repo),
            reading_service=ReadingService(
                device_repo, reading_repo, calibration_repo, aquarium_device_repo
            ),
            aquarium_service=AquariumService(aquarium_repo),
            aquarium_device_service=AquariumDeviceService(
                aquarium_repo, device_repo, aquarium_device_repo, calibration_repo
            ),
            calibration_repo=calibration_repo,
            aquarium_device_repo=aquarium_device_repo,
        )
        await conn.close()
        return

    raise ValueError(f"Unknown backend {backend}")


@pytest.fixture
async def sqlite_persistence(tmp_path: Path) -> AsyncIterator[tuple[ServiceBundle, Path]]:
    """
    Yields a service bundle bound to a persistent SQLite file, and the path.
    """
    db_path = tmp_path / "persist.db"
    conn = await aiosqlite.connect(db_path)
    await init_db(db_path, conn)
    await conn.execute(
        """
        INSERT OR IGNORE INTO users (id, email, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "00000000-0000-0000-0000-000000000000",
            "test-owner@example.com",
            hash_password("password"),
            1,
            datetime.utcnow().isoformat(),
        ),
    )
    await conn.commit()
    device_repo = SqliteDeviceRepository(conn)
    reading_repo = SqliteReadingRepository(conn)
    calibration_repo = SqlitePhCalibrationRepository(conn)
    aquarium_repo = SqliteAquariumRepository(conn)
    aquarium_device_repo = SqliteAquariumDeviceRepository(conn)
    bundle = ServiceBundle(
        device_service=DeviceService(device_repo),
        reading_service=ReadingService(device_repo, reading_repo, calibration_repo, aquarium_device_repo),
        aquarium_service=AquariumService(aquarium_repo),
        aquarium_device_service=AquariumDeviceService(
            aquarium_repo, device_repo, aquarium_device_repo, calibration_repo
        ),
        calibration_repo=calibration_repo,
        aquarium_device_repo=aquarium_device_repo,
    )
    yield bundle, db_path
    await conn.close()


def _override_jwt_dependency() -> dict:
    return {"sub": "00000000-0000-0000-0000-000000000000"}


async def _override_device_api_key_dependency(request: Request) -> UUID:
    device_id = request.path_params.get("device_id", "00000000-0000-0000-0000-000000000000")
    return UUID(device_id)


class _TestAssociationService:
    def __init__(self, device_service: DeviceService) -> None:
        self.device_service = device_service

    async def list_devices_for_user(self, _user_id: UUID):
        devices = await self.device_service.list_devices()
        return [d.id for d in devices]

    async def list_devices_for_aquarium(self, _user_id: UUID, _aquarium_id: UUID):
        devices = await self.device_service.list_devices()
        return [d.id for d in devices]


def _override_aquarium_device_service(request: Request):
    service = getattr(request.app.state, "device_service", None)
    return _TestAssociationService(service)


app.dependency_overrides.update(
    {
        jwt_dependency: _override_jwt_dependency,
        device_api_key_dependency: _override_device_api_key_dependency,
        readings_aquarium_device_service: _override_aquarium_device_service,
        devices_aquarium_device_service: _override_aquarium_device_service,
    }
)
