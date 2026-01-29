# Technologies

This project uses small, proven building blocks that run well on home servers while staying scalable.

## Backend (current)
- **FastAPI** — async API framework with clear typing and OpenAPI docs.
- **Pydantic v2** — strict request/response validation and settings management.
- **Uvicorn** — lightweight ASGI server for async workloads.
- **SQLAlchemy (async)** — consistent data access across SQLite and MariaDB.
- **Alembic** — schema migrations for MariaDB deployments.
- **aiosqlite / asyncmy / PyMySQL** — runtime and migration drivers.
- **PyJWT + bcrypt** — JWT auth and secure password hashing.
- **python-json-logger** — structured logs for operational visibility.

## Testing & quality (current)
- **pytest + httpx** — API and service tests with real HTTP flows.
- **ruff + black** — linting and formatting for consistent code style.

## Self‑hosting (current)
- **Docker + Compose** — reproducible local and production setups.

## Frontend (planned)
- **Next.js** — server‑rendered dashboard with fast navigation.
- **Charting library** — time‑series visualization (final choice documented when added).

If you want a different toolchain, open an issue with your constraints and target environment.

See also:
- [Architecture](architecture.md)
- [Backend overview](backend/README.md)
