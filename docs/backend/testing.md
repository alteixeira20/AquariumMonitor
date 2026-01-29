# Testing

The test suite is designed to protect the API contract, the domain rules, and storage behavior.

Keywords: `tests` `api contract` `domain rules` `persistence` `pytest`
Back: [Docs hub](../README.md)

## How to run
- `make test` — in‑memory backend (fast feedback)
- `make test-sqlite` — SQLite backend + seeded database

## What it validates
- **API contract**: real HTTP requests against FastAPI endpoints.
  - Status codes, response shapes, auth enforcement, and pagination rules.
- **Service logic**: ownership checks, calibration requirements, attachment rules.
- **Domain rules**: sensor range validation and deterministic calculations.
- **Persistence**: ordering, pagination, latest reading, and FK integrity.

## Failure output
- Each test prints a short pass/fail line.
- Full tracebacks are written to `logs/test.log`.

## Why this matters
These tests ensure that dashboards and devices can rely on a stable contract, and that invalid readings never reach storage.
