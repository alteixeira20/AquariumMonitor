#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-backups}
TS=$(date +%Y%m%d_%H%M%S)

DB_HOST=${DB_HOST:-127.0.0.1}
DB_PORT=${DB_PORT:-3306}
DB_NAME=${DB_NAME:-aquarium}
DB_USER=${DB_USER:-aquarium_app}
DB_PASSWORD=${DB_PASSWORD:-change-me}

mkdir -p "${BACKUP_DIR}"

mariadb-dump -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" \
  > "${BACKUP_DIR}/db.${TS}.sql"

echo "MariaDB backup written to ${BACKUP_DIR}/db.${TS}.sql"
