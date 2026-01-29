# Operations runbook

## Start / stop
SQLite:
```
docker compose -f infra/docker-compose.sqlite.yml up -d

docker compose -f infra/docker-compose.sqlite.yml down
```

MariaDB:
```
docker compose -f infra/docker-compose.yml up -d

docker compose -f infra/docker-compose.yml down
```

## Logs
```
docker logs -f aquariummonitor_backend
```

## Health checks
```
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/readiness
```

## Metrics
```
curl http://localhost:8000/v1/metrics/prometheus
```

## Backups
SQLite:
```
./scripts/backup_sqlite.sh
```

MariaDB:
```
./scripts/backup_mariadb.sh
```

Script env:
- `DB_PATH` and `BACKUP_DIR` for SQLite
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` for MariaDB

## Restore
SQLite:
```
./scripts/restore_sqlite.sh backups/app.db.YYYYMMDD_HHMMSS
```

MariaDB:
```
./scripts/restore_mariadb.sh backups/db.YYYYMMDD_HHMMSS.sql
```
