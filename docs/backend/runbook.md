# Operations runbook

## Start / stop
SQLite:
```
docker compose -f docker-compose.sqlite.yml up -d

docker compose -f docker-compose.sqlite.yml down
```

MariaDB:
```
docker compose up -d

docker compose down
```

## Logs
```
docker logs -f aquamonitor_backend
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

## Restore
SQLite:
```
./scripts/restore_sqlite.sh backups/app.db.YYYYMMDD_HHMMSS
```

MariaDB:
```
./scripts/restore_mariadb.sh backups/db.YYYYMMDD_HHMMSS.sql
```
