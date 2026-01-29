# Code tour

A quick map of the backend codebase.

## Entry point
- `app/main.py` — creates the FastAPI app, installs middleware, and wires services.

## API layer
- `app/api/router.py` — mounts all `/v1` routes.
- `app/api/v1/*` — request/response validation and handlers.

## Services
- `ReadingService` — validation, pH/TDS computation, persistence.
- `AquariumStatsService` — aggregate stats across devices.
- `DeviceStatusService` — online/offline status.
- `DeviceApiKeyService` — create/resolve/revoke device keys.
- `PhCalibrationService` — calibration lifecycle.
- `AquariumDeviceService` — attach/detach rules.

## Repositories
- `app/repositories/sqlite_repository.py`
- `app/repositories/mariadb_repository.py`
- `app/repositories/memory_repository.py`

## Domain
- `app/domain/reading.py` — sensor math and validation.
- `app/domain/ph_calibration.py` — calibration data model.
- `app/domain/device.py` / `aquarium.py` / `user.py`

## Infrastructure
- `app/infrastructure/db.py` — SQLAlchemy engine + sessions.
- `app/infrastructure/db_models.py` — ORM models.
- `alembic/` — migrations for MariaDB.

## Core utilities
- `app/core/config.py` — environment settings.
- `app/core/auth.py` — JWT + demo access.
- `app/core/security.py` — hashing utilities.
- `app/core/logging.py` — request logging.
- `app/core/metrics.py` — counters and Prometheus output.
- `app/core/backup.py` — SQLite backup loop.
