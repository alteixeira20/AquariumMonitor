# Testing

The test suite is designed to protect the API contract, the domain rules, and storage behavior.

## How to run
- `make test` — in‑memory backend (fast feedback)
- `make test-sqlite` — SQLite backend + seeded database

From the repo root, you can also run:
- `make backend-test`
- `make backend-test-sqlite`

## Manual smoke test (API)
The manual tester performs a full setup → login → device → calibration → reading flow.

Prerequisites:
- `curl` and `jq`
- API running locally (see below)

Run:
```
ADMIN_EMAIL=owner@example.com ADMIN_PASSWORD=change-me \
apps/backend/scripts/manual_test.sh
```

Notes:
- Uses `BASE_URL` (default: `http://localhost:8000`)
- If the instance is unconfigured, the script runs setup first

## Starting the API locally
From `apps/backend`:
```
make install
make dev
```

From the repo root:
```
make backend-dev
```

## What it validates
- **API contract**: real HTTP requests against FastAPI endpoints.
  - Status codes, response shapes, auth enforcement, and pagination rules.
- **Service logic**: ownership checks, calibration requirements, attachment rules.
- **Domain rules**: sensor range validation and deterministic calculations.
- **Persistence**: ordering, pagination, latest reading, and FK integrity.

## Coverage map
Covered:
- API endpoints (auth, devices, aquariums, readings, stats, health)
- Domain computations (pH and TDS validation and bounds)
- Storage behavior (SQLite persistence and ordering)
- Security constraints (single‑owner mode, rate limiting)

Not covered (by design):
- Frontend UI behavior
- Device firmware behavior
- Load testing or high‑throughput ingestion
- Network/security hardening beyond basic auth and rate limiting

## Production data note
Tests and seeds only exist for development and CI. In production, the database is populated by:
- Owner setup and user actions (aquariums, devices, calibration)
- Device or simulator readings sent to the API

## Failure output
- Each test prints a short pass/fail line.
- Full tracebacks are written to `logs/test.log`.

## Why this matters
These tests ensure that dashboards and devices can rely on a stable contract, and that invalid readings never reach storage.
