# Architecture

AquariumMonitor is a single‑owner, self‑hosted system that ingests aquarium sensor data and serves it to a web dashboard. The backend is intentionally simple and strict: clear domain rules, a service layer that enforces them, and storage that can run on SQLite by default or MariaDB when needed.

## System overview
- **Device or simulator** sends readings (temperature, pH voltage, TDS voltage).
- **Backend API** validates and stores readings, enforces calibration and attachment rules.
- **Storage** persists users, aquariums, devices, readings, and calibration data.
- **Web dashboard** queries stats and time‑series data for visualization.

## Backend layers
- **API layer** (FastAPI): routing, auth, validation, response shaping.
- **Domain layer**: sensor math, calibration, and invariants.
- **Service layer**: orchestration of domain rules and persistence.
- **Repository layer**: SQLite / MariaDB / memory implementations.
- **Infrastructure**: migrations, logging, metrics, backups.

## Core flows
### First‑run setup
1) If no owner exists, the UI calls the setup endpoint.
2) The owner account is created and stored with bcrypt.
3) If demo access is enabled in configuration, the UI can offer a demo login option.

### Device onboarding
1) Register a device.
2) Record pH calibration points (4.01 / 6.86 / 9.18).
3) Attach the device to an aquarium.
4) Device can now submit readings.

### Telemetry
1) Device submits a reading with its API key.
2) Service layer validates values and checks calibration + attachment.
3) Repository stores readings; stats endpoints provide medians and time‑series.

## Storage strategy
- **SQLite (default)** for easy self‑hosting.
- **MariaDB (optional)** for larger deployments.
- **Migrations** via Alembic to keep schema consistent on MariaDB.
- **Backups** for SQLite with a rolling retention window.

## Observability
- Structured JSON logs
- Health, readiness, and metrics endpoints
- Prometheus‑compatible metrics output

## Extensibility
- Add sensors by extending domain rules + schemas.
- Add dashboards without touching domain logic.
- Add a new database by implementing repository interfaces.

Related docs:
- `docs/backend/README.md`
- `docs/technologies.md`
- `docs/self_hosting.md`
