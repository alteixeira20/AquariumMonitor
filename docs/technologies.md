# Technologies

This project favors simple, proven tools that run well on small hardware while still scaling when needed.

## Backend
- **FastAPI** — async API framework; fast to build, good type hints, great OpenAPI support.
- **Pydantic (v2)** — request/response validation and settings, keeps data contracts strict and explicit.
- **Uvicorn** — lightweight ASGI server; handles async workloads without heavy ops overhead.

## Data & Persistence
- **SQLite (default)** — zero-config storage that fits self-hosting and home setups.
- **MariaDB (optional)** — drop-in upgrade for larger deployments and better concurrency.
- **SQLAlchemy (async)** — consistent data access layer across SQLite and MariaDB.
- **Alembic** — predictable schema migrations without manual SQL drift.
- **aiosqlite / asyncmy / PyMySQL** — async drivers for runtime, sync driver for migrations.

## Auth & Security
- **JWT (PyJWT)** — stateless tokens for API and UI auth flows.
- **bcrypt** — safe password hashing for the owner account.
- **Rate limiting** — simple middleware to protect the API from abuse.

## Observability
- **Structured JSON logs** — production-friendly logs that are easy to parse and ship.
- **Metrics endpoints** — lightweight internal metrics + Prometheus-compatible output.

## Dev & Quality
- **pytest + httpx** — fast API and service tests with realistic HTTP calls.
- **ruff + black** — consistent linting and formatting to keep the codebase clean.

## Delivery
- **Docker / Compose** — reproducible local and self-hosting installs.

If you want a specific technology replaced, open an issue and explain the target environment and constraints.
