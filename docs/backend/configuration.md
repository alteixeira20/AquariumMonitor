# Configuration

All configuration is driven by environment variables (see `apps/backend/.env.example`).

## Core
- `ENVIRONMENT`: `dev` | `test` | `prod`
- `DEBUG`: `true` / `false`
- `PROJECT_NAME`, `PROJECT_DESCRIPTION`, `VERSION`

## Storage
- `STORAGE_BACKEND`: `sqlite` | `mariadb` | `memory`

### SQLite
- `DATABASE_URL` (e.g., `sqlite:///./data/app.db`)
- `SQLITE_JOURNAL_MODE` (default: `WAL`)
- `SQLITE_SYNCHRONOUS` (default: `FULL`)
- `SQLITE_BUSY_TIMEOUT_MS` (default: `5000`)
- `BACKUP_ENABLED` (default: `true`)
- `BACKUP_DIR` (default: `backups`)
- `BACKUP_RETENTION_DAYS` (default: `7`)
- `BACKUP_INTERVAL_HOURS` (default: `6`)

These settings are applied at startup. A future UI setup wizard can surface them as prompts for new installs.

Planned setup flow:
- Choose database backend (SQLite default, optional MariaDB/Postgres)
- Collect connection settings for the chosen backend
- Verify the connection before proceeding

### MariaDB
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DB_ROOT_PASSWORD` (Docker only)

## Auth & security
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_SECONDS`
- `DEVICE_API_KEY_PEPPER`
- `DEMO_ENABLED` (default: `true`)
- `DEMO_USERNAME`, `DEMO_PASSWORD`, `DEMO_USER_ID`

## Single‑owner mode (optional)
- `SINGLE_OWNER_MODE`: `true` / `false`
- `OWNER_EMAIL` or `OWNER_USER_ID` (one is required when enabled)

## CORS
- `CORS_ORIGINS`
- `CORS_ALLOW_CREDENTIALS`
- `CORS_ALLOW_METHODS`
- `CORS_ALLOW_HEADERS`

## Rate limiting (optional)
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_REQUESTS`
- `RATE_LIMIT_WINDOW_SECONDS`

## Seeding
- `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`
