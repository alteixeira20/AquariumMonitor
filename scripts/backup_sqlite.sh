#!/usr/bin/env bash
set -euo pipefail

DB_PATH=${DB_PATH:-data/app.db}
BACKUP_DIR=${BACKUP_DIR:-backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
TS=$(date +%Y%m%d_%H%M%S)

mkdir -p "${BACKUP_DIR}"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "SQLite DB not found at ${DB_PATH}"
  exit 1
fi

cp "${DB_PATH}" "${BACKUP_DIR}/app.db.${TS}"
find "${BACKUP_DIR}" -type f -name "app.db.*" -mtime +"${RETENTION_DAYS}" -delete
echo "SQLite backup written to ${BACKUP_DIR}/app.db.${TS}"
