# Self‑hosting guide

AquariumMonitor is designed for single‑node hosting (home server or Raspberry Pi). SQLite is the default; MariaDB is optional.

## Prerequisites
- Docker + Docker Compose
- Port 8000 available (or use a reverse proxy)

## Configure
1) Copy env file:
   ```
   cp apps/backend/.env.example apps/backend/.env
   ```
2) Set secrets:
   - `JWT_SECRET`
   - `DEVICE_API_KEY_PEPPER`
3) Optional settings:
   - `DEMO_ENABLED=true` to allow demo login
   - `SINGLE_OWNER_MODE=true` to restrict access
   - `RATE_LIMIT_ENABLED=true` to rate‑limit API calls
4) SQLite backup policy (optional):
   - `BACKUP_ENABLED=true`
   - `BACKUP_INTERVAL_HOURS=6`
   - `BACKUP_RETENTION_DAYS=7`

## SQLite (recommended)
```
make prod
```

SQLite data lives in `apps/backend/data/app.db`.

## MariaDB (optional)
```
docker compose -f infra/docker-compose.yml up -d --build
```

## Simulator (optional)
The simulator runs in its own container and uses the owner account to provision demo data.
```
cp apps/simulator/.env.example apps/simulator/.env
cp apps/simulator/config.example.toml apps/simulator/config.toml
docker compose -f infra/docker-compose.sqlite.yml --profile simulator up -d
```

Convenience:
```
make prod-sim
```

## First‑run setup
- Create the owner account with `POST /v1/setup`.
- Demo login is controlled by `DEMO_ENABLED` and exposed during setup if enabled.

## Health checks
- `GET /v1/health`
- `GET /v1/readiness`
- `GET /v1/metrics/prometheus`

## Backups
SQLite:
```
./scripts/backup_sqlite.sh
```

MariaDB:
```
./scripts/backup_mariadb.sh
```

Script env (optional):
- `DB_PATH` and `BACKUP_DIR` for SQLite
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` for MariaDB

See also:
- [Backend configuration](backend/configuration.md)
