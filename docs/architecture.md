# Architecture

AquariumMonitor is a single‑owner, self‑hosted monitoring platform. The backend is intentionally simple: strict domain rules, a clean service layer, and a storage abstraction that works on SQLite by default and MariaDB when you need more scale.

## High-level design
- **API layer (FastAPI)** — HTTP endpoints, auth, validation, and response shaping.
- **Domain layer** — business rules (calibration, reading validation, device state).
- **Service layer** — orchestration of domain rules + persistence (use cases).
- **Repository layer** — data access abstraction (SQLite / MariaDB / memory).
- **Infrastructure** — migrations, backup jobs, metrics, logging.

## Core flows
### First-run setup
1) If no owner exists, the UI calls the setup endpoint.
2) An owner account is created and stored with bcrypt.
3) Demo read‑only access becomes available for previews.

### Device onboarding
1) Register a device.
2) Attach it to an aquarium after pH calibration is stored (4.01 / 6.86 / 9.18).
3) Once attached and calibrated, the device can send readings.

### Telemetry
1) Device sends readings to the API.
2) Service layer validates values and enforces calibration requirements.
3) Repository persists readings; stats endpoints provide medians and time-series.

## Request lifecycle (simplified)
1) **Auth middleware** resolves owner vs demo access.
2) **Validation** (Pydantic) checks input contracts.
3) **Service** applies domain rules.
4) **Repository** persists or retrieves data.
5) **Response** is shaped and logged.

## Storage strategy
- **SQLite is the default** for zero‑config self‑hosting.
- **MariaDB is optional** for higher write throughput.
- **Alembic migrations** keep schemas consistent across backends.

See: `docs/technologies.md` and `docs/configuration.md`.

## Observability
- **Structured JSON logs** for operational visibility.
- **Metrics endpoints** for quick health inspection and Prometheus scraping.

## Background tasks
- **SQLite backups** are created on a schedule and pruned by retention.

## Extensibility
- Add new sensors by extending the domain rules + schemas.
- Add new storage backends by implementing repository interfaces.
- Add new UI features without changing core domain behavior.

## Related docs
- `docs/technologies.md`
- `docs/api.md` (coming next)
- `docs/testing.md` (coming next)
- `docs/self_hosting.md` (coming next)
