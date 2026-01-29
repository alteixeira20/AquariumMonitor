# Self‑hosting guide

AquariumMonitor is designed for single‑node hosting (home server or Raspberry Pi). SQLite is the default; MariaDB is optional.

## Prerequisites
- Docker + Docker Compose
- Port 8000 available (or use a reverse proxy)

## Configure
1) Copy env file:
   ```
   cp .env.example .env
   ```
2) Set secrets:
   - `JWT_SECRET`
   - `DEVICE_API_KEY_PEPPER`
3) Optional settings:
   - `DEMO_ENABLED=true` to allow demo login
   - `SINGLE_OWNER_MODE=true` to restrict access
   - `RATE_LIMIT_ENABLED=true` to rate‑limit API calls

## SQLite (recommended)
```
docker compose -f infra/docker-compose.sqlite.yml up -d --build
```

SQLite data lives in `./data/app.db`.

## MariaDB (optional)
```
docker compose -f infra/docker-compose.yml up -d --build
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

See also:
- [Backend configuration](backend/configuration.md)
