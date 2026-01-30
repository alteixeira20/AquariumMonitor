# Technologies

This project uses small, proven building blocks that run well on home servers while staying scalable.

## Backend (current)
<details>
<summary><strong>FastAPI</strong></summary>
Async API framework with strong typing and automatic OpenAPI docs. Chosen for speed, clarity, and a minimal learning curve for contributors.
</details>

<details>
<summary><strong>Pydantic v2</strong></summary>
Validates requests and responses with explicit schemas. Keeps API contracts strict and reduces silent data issues.
</details>

<details>
<summary><strong>Uvicorn</strong></summary>
Lightweight ASGI server that runs well on small hardware and handles async workloads efficiently.
</details>

<details>
<summary><strong>SQLAlchemy (async)</strong></summary>
Consistent data access layer across SQLite and MariaDB, which keeps storage changes contained to repository logic.
</details>

<details>
<summary><strong>Alembic</strong></summary>
Schema migrations for MariaDB deployments, so production stays consistent and versioned.
</details>

<details>
<summary><strong>aiosqlite / asyncmy / PyMySQL</strong></summary>
Async drivers for runtime and a sync driver for migrations, matching each backend’s needs.
</details>

<details>
<summary><strong>PyJWT + bcrypt</strong></summary>
JWTs for stateless auth and bcrypt for safe password hashing.
</details>

<details>
<summary><strong>python-json-logger</strong></summary>
Structured logs for production visibility and easy parsing in log pipelines.
</details>

## Testing & quality (current)
<details>
<summary><strong>pytest + httpx</strong></summary>
API and service tests that exercise real HTTP flows without a running server.
</details>

<details>
<summary><strong>ruff + black</strong></summary>
Consistent linting and formatting so the codebase stays predictable and easy to review.
</details>

## Self‑hosting (current)
<details>
<summary><strong>Docker + Compose</strong></summary>
Reproducible setups for local development and production, with predictable dependency versions.
</details>

## Frontend (current)
<details>
<summary><strong>Next.js</strong></summary>
App Router UI for a fast, structured dashboard that can scale to multi‑page workflows.
</details>

<details>
<summary><strong>TypeScript</strong></summary>
Strong typing for UI state, API responses, and shared domain models between screens.
</details>

<details>
<summary><strong>Tailwind CSS</strong></summary>
Utility‑first styling that keeps layout code close to the components and makes visual tweaks fast.
</details>

<details>
<summary><strong>Charting library</strong></summary>
Time‑series visualization for live and historical sensor data. Final choice documented when added.
</details>

If you want a different toolchain, open an issue with your constraints and target environment.

See also:
- [Architecture](architecture.md)
- [Backend overview](backend/README.md)
