#!/usr/bin/env sh
set -e

python3 - <<'PY'
import os
import sys
import time
import subprocess
import pymysql

storage_backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
if storage_backend == "sqlite":
    print("SQLite backend selected; skipping MariaDB migrations")
    raise SystemExit(0)

host = os.getenv("DB_HOST", "localhost")
port = int(os.getenv("DB_PORT", "3306"))
user = os.getenv("DB_USER", "")
password = os.getenv("DB_PASSWORD", "")
name = os.getenv("DB_NAME", "")

lock_name = f"{name or 'aquarium'}_alembic_migrations"
required_tables = {
    "users",
    "aquariums",
    "devices",
    "readings",
    "aquarium_devices",
    "device_api_keys",
    "device_ph_calibrations",
}

attempts = 30
conn = None
for attempt in range(attempts):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=name)
        print("MariaDB connection ready")
        break
    except Exception as exc:
        if attempt == attempts - 1:
            print(f"MariaDB connection failed: {exc}", file=sys.stderr)
            raise
        print(f"Waiting for MariaDB... ({exc})")
        time.sleep(2)

# DB-level lock prevents concurrent Alembic migrations if multiple containers start together.
# This is idempotent: migrations are safe to run multiple times and serialized by this lock.
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 30);", (lock_name,))
        row = cursor.fetchone()
        if row is None or row[0] != 1:
            print("Failed to acquire migration lock; another instance may be running migrations", file=sys.stderr)
            raise RuntimeError("Failed to acquire migration lock")

    result = subprocess.run(["alembic", "upgrade", "head"], check=False)
    if result.returncode != 0:
        print(f"Alembic migration failed with exit code {result.returncode}", file=sys.stderr)
        raise RuntimeError(f"Alembic migration failed with exit code {result.returncode}")

    # Fail startup if core tables are missing; prevents serving API on partial schema.
    with conn.cursor() as cursor:
        placeholders = ",".join(["%s"] * len(required_tables))
        cursor.execute(
            f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name IN ({placeholders})
            """,
            (name, *sorted(required_tables)),
        )
        found = {row[0] for row in cursor.fetchall()}
        missing = sorted(required_tables - found)
        if missing:
            print(f"Schema invalid after migration, missing tables: {missing}", file=sys.stderr)
            raise RuntimeError(f"Schema invalid after migration, missing tables: {missing}")
finally:
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT RELEASE_LOCK(%s);", (lock_name,))
        except Exception as exc:
            print(f"Failed to release migration lock: {exc}", file=sys.stderr)
        conn.close()
PY

python3 scripts/seed_user.py

exec "$@"
