#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE=${1:-}

if [[ -z "${BACKUP_FILE}" ]]; then
  echo "Usage: ./scripts/restore_mariadb.sh <backup-file.sql>"
  exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

DB_HOST=${DB_HOST:-127.0.0.1}
DB_PORT=${DB_PORT:-3306}
DB_NAME=${DB_NAME:-aquarium}
DB_USER=${DB_USER:-aquarium_app}
DB_PASSWORD=${DB_PASSWORD:-change-me}

cat "${BACKUP_FILE}" | mariadb -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}"
echo "MariaDB restored from ${BACKUP_FILE}"
