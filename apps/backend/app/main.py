from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.router import api_router
from app.core.backup import backup_loop, resolve_sqlite_path
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    DomainError,
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
    value_error_handler,
)
from app.core.logging import configure_logging, install_request_logging
from app.core.middleware import add_cors, add_rate_limit
from app.core.security_headers import add_security_headers
from app.infrastructure.db import create_mariadb_engine, create_session_factory
from app.repositories.mariadb_repository import (
    MariaDbAquariumDeviceRepository,
    MariaDbAquariumRepository,
    MariaDbDeviceApiKeyRepository,
    MariaDbDeviceRepository,
    MariaDbPhCalibrationRepository,
    MariaDbReadingRepository,
    MariaDbUserRepository,
)
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    DeviceApiKeyRepository,
    DeviceRepository,
    PhCalibrationRepository,
    ReadingRepository,
    UserRepository,
)
from app.repositories.memory_repository import (
    MemoryAquariumDeviceRepository,
    MemoryAquariumRepository,
    MemoryDeviceApiKeyRepository,
    MemoryDeviceRepository,
    MemoryPhCalibrationRepository,
    MemoryReadingRepository,
    MemoryUserRepository,
)
from app.repositories.sqlite_repository import (
    SqliteAquariumDeviceRepository,
    SqliteAquariumRepository,
    SqliteDeviceApiKeyRepository,
    SqliteDeviceRepository,
    SqlitePhCalibrationRepository,
    SqliteReadingRepository,
    SqliteUserRepository,
    init_db,
)
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.aquarium_service import AquariumService
from app.services.aquarium_stats_service import AquariumStatsService
from app.services.device_api_key_service import DeviceApiKeyService
from app.services.device_service import DeviceService
from app.services.device_status_service import DeviceStatusService
from app.services.ph_calibration_service import PhCalibrationService
from app.services.reading_service import ReadingService
from app.services.user_service import UserService

def _init_services(
    app: FastAPI,
    *,
    device_repo: DeviceRepository,
    reading_repo: ReadingRepository,
    ph_calibration_repo: PhCalibrationRepository,
    device_api_key_repo: DeviceApiKeyRepository,
    user_repo: UserRepository,
    aquarium_repo: AquariumRepository,
    aquarium_device_repo: AquariumDeviceRepository,
) -> None:
    app.state.device_service = DeviceService(device_repo)
    app.state.reading_service = ReadingService(
        device_repo,
        reading_repo,
        ph_calibration_repo,
        aquarium_device_repo,
    )
    app.state.device_api_key_service = DeviceApiKeyService(
        device_repo, device_api_key_repo
    )
    app.state.user_service = UserService(user_repo)
    app.state.aquarium_service = AquariumService(aquarium_repo)
    app.state.aquarium_device_service = AquariumDeviceService(
        aquarium_repo,
        device_repo,
        aquarium_device_repo,
        ph_calibration_repo,
    )
    app.state.aquarium_stats_service = AquariumStatsService(
        aquarium_repo,
        aquarium_device_repo,
        reading_repo,
    )
    app.state.device_status_service = DeviceStatusService(
        aquarium_repo,
        aquarium_device_repo,
        reading_repo,
    )
    app.state.ph_calibration_service = PhCalibrationService(
        device_repo,
        aquarium_repo,
        aquarium_device_repo,
        reading_repo,
        ph_calibration_repo,
    )

def _reset_app_state(app: FastAPI) -> None:
    app.state.db_path = None
    app.state.db_engine = None
    app.state.db_session_factory = None
    app.state.user_service = None
    app.state.aquarium_service = None
    app.state.aquarium_device_service = None
    app.state.device_api_key_service = None
    app.state.aquarium_stats_service = None
    app.state.device_status_service = None
    app.state.ph_calibration_service = None
    app.state.user_service = None
    app.state.db_conn = None
    app.state.backup_task = None


def _should_run_backups(settings: Settings) -> bool:
    if settings.environment == "test":
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return settings.backup_enabled


async def _init_sqlite_backend(app: FastAPI, settings: Settings) -> aiosqlite.Connection:
    db_path = resolve_sqlite_path(settings.database_url)
    os.makedirs(db_path.parent, exist_ok=True)
    db_conn = await aiosqlite.connect(
        str(db_path), timeout=settings.sqlite_busy_timeout_ms / 1000
    )
    await init_db(
        str(db_path),
        db_conn,
        journal_mode=settings.sqlite_journal_mode,
        synchronous=settings.sqlite_synchronous,
        busy_timeout_ms=settings.sqlite_busy_timeout_ms,
    )

    sqlite_device_repo = SqliteDeviceRepository(db_conn)
    sqlite_reading_repo = SqliteReadingRepository(db_conn)
    sqlite_ph_calibration_repo = SqlitePhCalibrationRepository(db_conn)
    sqlite_device_api_key_repo = SqliteDeviceApiKeyRepository(db_conn)
    sqlite_user_repo = SqliteUserRepository(db_conn)
    sqlite_aquarium_repo = SqliteAquariumRepository(db_conn)
    sqlite_aquarium_device_repo = SqliteAquariumDeviceRepository(db_conn)

    _init_services(
        app,
        device_repo=sqlite_device_repo,
        reading_repo=sqlite_reading_repo,
        ph_calibration_repo=sqlite_ph_calibration_repo,
        device_api_key_repo=sqlite_device_api_key_repo,
        user_repo=sqlite_user_repo,
        aquarium_repo=sqlite_aquarium_repo,
        aquarium_device_repo=sqlite_aquarium_device_repo,
    )
    app.state.db_conn = db_conn
    app.state.db_path = db_path
    return db_conn


def _init_mariadb_backend(app: FastAPI, settings: Settings) -> None:
    engine = create_mariadb_engine(settings)
    session_factory = create_session_factory(engine)
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory

    mariadb_device_repo = MariaDbDeviceRepository(session_factory)
    mariadb_reading_repo = MariaDbReadingRepository(session_factory)
    mariadb_user_repo = MariaDbUserRepository(session_factory)
    mariadb_aquarium_repo = MariaDbAquariumRepository(session_factory)
    mariadb_aquarium_device_repo = MariaDbAquariumDeviceRepository(session_factory)
    mariadb_api_key_repo = MariaDbDeviceApiKeyRepository(session_factory)
    mariadb_ph_calibration_repo = MariaDbPhCalibrationRepository(session_factory)

    _init_services(
        app,
        device_repo=mariadb_device_repo,
        reading_repo=mariadb_reading_repo,
        ph_calibration_repo=mariadb_ph_calibration_repo,
        device_api_key_repo=mariadb_api_key_repo,
        user_repo=mariadb_user_repo,
        aquarium_repo=mariadb_aquarium_repo,
        aquarium_device_repo=mariadb_aquarium_device_repo,
    )


def _init_memory_backend(app: FastAPI) -> None:
    memory_device_repo = MemoryDeviceRepository()
    memory_reading_repo = MemoryReadingRepository()
    memory_ph_calibration_repo = MemoryPhCalibrationRepository()
    memory_device_api_key_repo = MemoryDeviceApiKeyRepository()
    memory_user_repo = MemoryUserRepository()
    memory_aquarium_repo = MemoryAquariumRepository()
    memory_aquarium_device_repo = MemoryAquariumDeviceRepository()

    _init_services(
        app,
        device_repo=memory_device_repo,
        reading_repo=memory_reading_repo,
        ph_calibration_repo=memory_ph_calibration_repo,
        device_api_key_repo=memory_device_api_key_repo,
        user_repo=memory_user_repo,
        aquarium_repo=memory_aquarium_repo,
        aquarium_device_repo=memory_aquarium_device_repo,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Runs once at startup and once at shutdown.

    Use this to initialize:
      - database connections
      - caches
      - background tasks
    """
    settings = get_settings()

    # Startup
    configure_logging(settings=settings)

    db_conn = None
    _reset_app_state(app)
    if settings.storage_backend == "sqlite":
        db_conn = await _init_sqlite_backend(app, settings)
    elif settings.storage_backend == "mariadb":
        _init_mariadb_backend(app, settings)
    else:
        _init_memory_backend(app)

    if settings.storage_backend == "sqlite" and _should_run_backups(settings):
        db_path = getattr(app.state, "db_path", None)
        if db_path:
            app.state.backup_task = asyncio.create_task(
                backup_loop(settings, Path(db_path))
            )

    yield

    # Shutdown
    backup_task = getattr(app.state, "backup_task", None)
    if backup_task:
        backup_task.cancel()
        try:
            await backup_task
        except asyncio.CancelledError:
            pass
    if db_conn:
        await db_conn.close()
    if app.state.db_engine is not None:
        await app.state.db_engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description=settings.project_description,
        contact={"name": "Maintainer"},
        license_info={"name": "CC BY-NC 4.0"},
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Mount API exactly as tests expect (NO extra /api prefix)
    app.include_router(api_router)

    # Default to memory-backed services before lifespan runs.
    _init_memory_backend(app)

    # Middleware & exception handlers
    install_request_logging(app)
    add_cors(app, settings)
    add_rate_limit(app, settings)
    add_security_headers(app)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    return app


# This is what pytest imports: from app.main import app
app = create_app()
