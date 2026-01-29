# Storage and backups

AquariumMonitor supports SQLite by default and MariaDB as an optional upgrade.

## SQLite (default)
- Best fit for single‑node self‑hosting.
- Uses runtime schema creation for fast setup.
- Durable by default (WAL + FULL sync).
- Backups are supported with a rolling retention window.
- New columns are added automatically on startup when the schema evolves.

Key settings:
- `DATABASE_URL=sqlite:///./data/app.db`
- `SQLITE_JOURNAL_MODE=WAL`
- `SQLITE_SYNCHRONOUS=FULL`
- `SQLITE_BUSY_TIMEOUT_MS=5000`
- `BACKUP_ENABLED=true`
- `BACKUP_RETENTION_DAYS=7`
- `BACKUP_INTERVAL_HOURS=6`

## MariaDB (optional)
- Use for higher write throughput or multi‑client access.
- Schema managed by Alembic migrations.
- The backend does not create databases or users.

Key settings:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

## Backup strategy
- SQLite backups run on a schedule and keep a rolling buffer.
- Old backups are pruned automatically based on retention.
- MariaDB backups use `mysqldump` via scripts.

Manual scripts:
- `scripts/backup_sqlite.sh`
- `scripts/backup_mariadb.sh`
- `scripts/restore_sqlite.sh`
- `scripts/restore_mariadb.sh`
