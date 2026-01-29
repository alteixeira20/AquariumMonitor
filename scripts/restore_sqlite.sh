#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE=${1:-}
DB_PATH=${DB_PATH:-data/app.db}

if [[ -z "${BACKUP_FILE}" ]]; then
  echo "Usage: ./scripts/restore_sqlite.sh <backup-file>"
  exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

mkdir -p "$(dirname "${DB_PATH}")"
cp "${BACKUP_FILE}" "${DB_PATH}"
echo "SQLite restored to ${DB_PATH}"
