from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import aiosqlite

from app.domain.aquarium import Aquarium
from app.domain.device import Device
from app.domain.ph_calibration import PhCalibrationPoint
from app.domain.reading import Reading
from app.domain.user import User
from app.core.security import hash_password
from app.repositories.base_repository import (
    AquariumDeviceRepository,
    AquariumRepository,
    DeviceRepository,
    DeviceApiKeyRepository,
    PhCalibrationRepository,
    ReadingRepository,
    UserRepository,
)

_ALLOWED_JOURNAL_MODES = {"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"}
_ALLOWED_SYNCHRONOUS = {"OFF", "NORMAL", "FULL", "EXTRA"}

_TEST_OWNER_ID = "00000000-0000-0000-0000-000000000000"
_TEST_OWNER_EMAIL = "test-owner@example.com"


async def _ensure_sqlite_columns(
    conn: aiosqlite.Connection,
    table: str,
    columns: dict[str, str],
) -> None:
    cursor = await conn.execute(f"PRAGMA table_info({table});")
    rows = await cursor.fetchall()
    await cursor.close()
    existing = {row[1] for row in rows}
    for column, col_type in columns.items():
        if column not in existing:
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};")
    await conn.commit()


async def init_db(
    db_path: str | Path,
    conn: aiosqlite.Connection | None = None,
    *,
    journal_mode: str = "WAL",
    synchronous: str = "FULL",
    busy_timeout_ms: int = 5000,
) -> None:
    """
    Initialize SQLite tables if they do not exist.

    Accepts either an existing connection or a path to open temporarily.
    """

    should_close = False
    if conn is None:
        conn = await aiosqlite.connect(db_path)
        should_close = True

    journal_mode = journal_mode.upper()
    synchronous = synchronous.upper()
    if journal_mode not in _ALLOWED_JOURNAL_MODES:
        journal_mode = "WAL"
    if synchronous not in _ALLOWED_SYNCHRONOUS:
        synchronous = "FULL"

    await conn.executescript(
        f"""
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = {journal_mode};
        PRAGMA synchronous = {synchronous};
        PRAGMA busy_timeout = {busy_timeout_ms};

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS aquariums (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            water_type TEXT NOT NULL,
            liters REAL NOT NULL,
            temperature_enabled INTEGER NOT NULL DEFAULT 1,
            temperature_min REAL NOT NULL,
            temperature_max REAL NOT NULL,
            ph_enabled INTEGER NOT NULL DEFAULT 1,
            ph_min REAL NOT NULL,
            ph_max REAL NOT NULL,
            tds_enabled INTEGER NOT NULL DEFAULT 1,
            tds_min REAL NOT NULL,
            tds_max REAL NOT NULL,
            filter_type TEXT,
            filter_flow_lph REAL,
            heater_watts REAL,
            lighting_type TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT,
            location TEXT,
            owner_user_id TEXT,
            claimed_at TEXT,
            is_active INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(owner_user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS aquarium_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            attached_at TEXT NOT NULL,
            detached_at TEXT,
            FOREIGN KEY(aquarium_id) REFERENCES aquariums(id),
            FOREIGN KEY(device_id) REFERENCES devices(id)
        );

        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            raw_ph_voltage REAL NOT NULL,
            raw_tds_voltage REAL NOT NULL,
            ph_value REAL NOT NULL,
            tds_ppm REAL NOT NULL,
            ph_calibrated INTEGER NOT NULL DEFAULT 0,
            received_at TEXT NOT NULL,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        );

        CREATE TABLE IF NOT EXISTS device_ph_calibrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ph_point REAL NOT NULL,
            voltage REAL NOT NULL,
            created_at TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        );

        CREATE TABLE IF NOT EXISTS device_api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            key_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            revoked_at TEXT,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        );

        CREATE INDEX IF NOT EXISTS idx_readings_device_id ON readings(device_id);
        CREATE INDEX IF NOT EXISTS idx_readings_received_at ON readings(received_at);
        CREATE INDEX IF NOT EXISTS idx_device_ph_calibrations_device_id
            ON device_ph_calibrations(device_id);
        CREATE INDEX IF NOT EXISTS idx_device_ph_calibrations_is_active
            ON device_ph_calibrations(is_active);
        CREATE INDEX IF NOT EXISTS idx_aquariums_user_id ON aquariums(user_id);
        CREATE INDEX IF NOT EXISTS idx_aquarium_devices_aquarium_id ON aquarium_devices(aquarium_id);
        CREATE INDEX IF NOT EXISTS idx_aquarium_devices_device_id ON aquarium_devices(device_id);
        CREATE INDEX IF NOT EXISTS idx_device_api_keys_device_id
            ON device_api_keys(device_id);
        CREATE INDEX IF NOT EXISTS idx_device_api_keys_key_hash
            ON device_api_keys(key_hash);
        """
    )

    await _ensure_sqlite_columns(
        conn,
        "aquariums",
        {
            "temperature_enabled": "INTEGER DEFAULT 1",
            "ph_enabled": "INTEGER DEFAULT 1",
            "tds_enabled": "INTEGER DEFAULT 1",
            "filter_type": "TEXT",
            "filter_flow_lph": "REAL",
            "heater_watts": "REAL",
            "lighting_type": "TEXT",
            "notes": "TEXT",
        },
    )
    await _ensure_sqlite_columns(
        conn,
        "devices",
        {
            "owner_user_id": "TEXT",
            "claimed_at": "TEXT",
        },
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_devices_owner_user_id ON devices(owner_user_id);"
    )
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ENVIRONMENT") == "test":
        await _seed_test_owner(conn)
    await conn.commit()

    if should_close:
        await conn.close()


async def _seed_test_owner(conn: aiosqlite.Connection) -> None:
    cursor = await conn.execute("SELECT id FROM users WHERE id = ?", (_TEST_OWNER_ID,))
    row = await cursor.fetchone()
    await cursor.close()
    if row is not None:
        return
    await conn.execute(
        """
        INSERT INTO users (id, email, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            _TEST_OWNER_ID,
            _TEST_OWNER_EMAIL,
            hash_password("password"),
            1,
            datetime.now(UTC).isoformat(),
        ),
    )


def _row_to_device(row: tuple[Any, ...]) -> Device:
    return Device(
        id=UUID(row[0]),
        name=row[1],
        location=row[2],
        owner_user_id=UUID(row[3]) if row[3] else None,
        claimed_at=datetime.fromisoformat(row[4]) if row[4] else None,
        is_active=bool(row[5]),
        created_at=datetime.fromisoformat(row[6]),
        updated_at=datetime.fromisoformat(row[7]),
    )


def _row_to_user(row: tuple[Any, ...]) -> User:
    return User(
        id=UUID(row[0]),
        email=row[1],
        password_hash=row[2],
        is_active=bool(row[3]),
        created_at=datetime.fromisoformat(row[4]),
    )


def _row_to_aquarium(row: tuple[Any, ...]) -> Aquarium:
    return Aquarium(
        id=UUID(row[0]),
        user_id=UUID(row[1]),
        name=row[2],
        water_type=row[3],
        liters=row[4],
        temperature_enabled=bool(row[5]) if row[5] is not None else True,
        temperature_min=row[6],
        temperature_max=row[7],
        ph_enabled=bool(row[8]) if row[8] is not None else True,
        ph_min=row[9],
        ph_max=row[10],
        tds_enabled=bool(row[11]) if row[11] is not None else True,
        tds_min=row[12],
        tds_max=row[13],
        filter_type=row[14],
        filter_flow_lph=row[15],
        heater_watts=row[16],
        lighting_type=row[17],
        notes=row[18],
        created_at=datetime.fromisoformat(row[19]),
    )


def _row_to_reading(row: tuple[Any, ...]) -> Reading:
    return Reading(
        device_id=UUID(row[1]),
        temperature_c=row[2],
        raw_ph_voltage=row[3],
        raw_tds_voltage=row[4],
        ph_value=row[5],
        tds_ppm=row[6],
        ph_calibrated=bool(row[7]),
        received_at=datetime.fromisoformat(row[8]),
    )


class SqliteUserRepository(UserRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get_by_email(self, email: str) -> User | None:
        cursor = await self._conn.execute(
            "SELECT id, email, password_hash, is_active, created_at FROM users WHERE LOWER(email) = ?",
            (email,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return _row_to_user(row)

    async def get_by_id(self, user_id: UUID) -> User | None:
        cursor = await self._conn.execute(
            "SELECT id, email, password_hash, is_active, created_at FROM users WHERE id = ?",
            (str(user_id),),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return _row_to_user(row)

    async def create(self, user: User) -> User:
        await self._conn.execute(
            """
            INSERT INTO users (id, email, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(user.id),
                user.email,
                user.password_hash,
                1 if user.is_active else 0,
                user.created_at.astimezone(UTC).isoformat(),
            ),
        )
        await self._conn.commit()
        return user

    async def count(self) -> int:
        cursor = await self._conn.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        await cursor.close()
        return int(row[0]) if row else 0

    async def get_first_user(self) -> User | None:
        cursor = await self._conn.execute(
            "SELECT id, email, password_hash, is_active, created_at FROM users ORDER BY created_at ASC LIMIT 1"
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return _row_to_user(row)


class SqliteAquariumRepository(AquariumRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, aquarium: Aquarium) -> Aquarium:
        created_at = aquarium.created_at.astimezone(UTC).isoformat()
        await self._conn.execute(
            """
            INSERT INTO aquariums (
                id, user_id, name, water_type, liters,
                temperature_enabled, temperature_min, temperature_max,
                ph_enabled, ph_min, ph_max,
                tds_enabled, tds_min, tds_max,
                filter_type, filter_flow_lph, heater_watts,
                lighting_type, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(aquarium.id),
                str(aquarium.user_id),
                aquarium.name,
                aquarium.water_type,
                aquarium.liters,
                1 if aquarium.temperature_enabled else 0,
                aquarium.temperature_min,
                aquarium.temperature_max,
                1 if aquarium.ph_enabled else 0,
                aquarium.ph_min,
                aquarium.ph_max,
                1 if aquarium.tds_enabled else 0,
                aquarium.tds_min,
                aquarium.tds_max,
                aquarium.filter_type,
                aquarium.filter_flow_lph,
                aquarium.heater_watts,
                aquarium.lighting_type,
                aquarium.notes,
                created_at,
            ),
        )
        await self._conn.commit()
        return aquarium

    async def list_for_user(self, user_id: UUID) -> list[Aquarium]:
        cursor = await self._conn.execute(
            """
            SELECT id, user_id, name, water_type, liters,
                   temperature_enabled, temperature_min, temperature_max,
                   ph_enabled, ph_min, ph_max,
                   tds_enabled, tds_min, tds_max,
                   filter_type, filter_flow_lph, heater_watts,
                   lighting_type, notes, created_at
            FROM aquariums
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (str(user_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_aquarium(r) for r in rows]

    async def get(self, aquarium_id: UUID) -> Aquarium | None:
        cursor = await self._conn.execute(
            """
            SELECT id, user_id, name, water_type, liters,
                   temperature_enabled, temperature_min, temperature_max,
                   ph_enabled, ph_min, ph_max,
                   tds_enabled, tds_min, tds_max,
                   filter_type, filter_flow_lph, heater_watts,
                   lighting_type, notes, created_at
            FROM aquariums
            WHERE id = ?
            """,
            (str(aquarium_id),),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return _row_to_aquarium(row)

    async def update(self, aquarium: Aquarium) -> Aquarium:
        await self._conn.execute(
            """
            UPDATE aquariums
            SET name = ?,
                water_type = ?,
                liters = ?,
                temperature_enabled = ?,
                temperature_min = ?,
                temperature_max = ?,
                ph_enabled = ?,
                ph_min = ?,
                ph_max = ?,
                tds_enabled = ?,
                tds_min = ?,
                tds_max = ?,
                filter_type = ?,
                filter_flow_lph = ?,
                heater_watts = ?,
                lighting_type = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                aquarium.name,
                aquarium.water_type,
                aquarium.liters,
                1 if aquarium.temperature_enabled else 0,
                aquarium.temperature_min,
                aquarium.temperature_max,
                1 if aquarium.ph_enabled else 0,
                aquarium.ph_min,
                aquarium.ph_max,
                1 if aquarium.tds_enabled else 0,
                aquarium.tds_min,
                aquarium.tds_max,
                aquarium.filter_type,
                aquarium.filter_flow_lph,
                aquarium.heater_watts,
                aquarium.lighting_type,
                aquarium.notes,
                str(aquarium.id),
            ),
        )
        await self._conn.commit()
        return aquarium

    async def delete(self, aquarium_id: UUID) -> None:
        await self._conn.execute(
            "DELETE FROM aquarium_devices WHERE aquarium_id = ?", (str(aquarium_id),)
        )
        await self._conn.execute(
            "DELETE FROM aquariums WHERE id = ?", (str(aquarium_id),)
        )
        await self._conn.commit()


class SqliteAquariumDeviceRepository(AquariumDeviceRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def attach(self, aquarium_id: UUID, device_id: UUID) -> None:
        attached_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            """
            INSERT INTO aquarium_devices (aquarium_id, device_id, attached_at, detached_at)
            VALUES (?, ?, ?, NULL)
            """,
            (str(aquarium_id), str(device_id), attached_at),
        )
        await self._conn.commit()

    async def detach(self, aquarium_id: UUID, device_id: UUID) -> None:
        detached_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            """
            UPDATE aquarium_devices
            SET detached_at = ?
            WHERE aquarium_id = ? AND device_id = ? AND detached_at IS NULL
            """,
            (detached_at, str(aquarium_id), str(device_id)),
        )
        await self._conn.commit()

    async def get_active_aquarium_for_device(self, device_id: UUID) -> UUID | None:
        cursor = await self._conn.execute(
            """
            SELECT aquarium_id
            FROM aquarium_devices
            WHERE device_id = ? AND detached_at IS NULL
            ORDER BY attached_at DESC
            LIMIT 1
            """,
            (str(device_id),),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return UUID(row[0])

    async def list_active_devices_for_aquarium(self, aquarium_id: UUID) -> list[UUID]:
        cursor = await self._conn.execute(
            """
            SELECT device_id
            FROM aquarium_devices
            WHERE aquarium_id = ? AND detached_at IS NULL
            """,
            (str(aquarium_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [UUID(row[0]) for row in rows]

    async def list_attachment_windows_for_aquarium(
        self, aquarium_id: UUID
    ) -> list[tuple[UUID, datetime, datetime | None]]:
        cursor = await self._conn.execute(
            """
            SELECT device_id, attached_at, detached_at
            FROM aquarium_devices
            WHERE aquarium_id = ?
            ORDER BY attached_at ASC
            """,
            (str(aquarium_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        windows: list[tuple[UUID, datetime, datetime | None]] = []
        for device_id, attached_at, detached_at in rows:
            windows.append(
                (
                    UUID(device_id),
                    datetime.fromisoformat(attached_at),
                    datetime.fromisoformat(detached_at) if detached_at else None,
                )
            )
        return windows


class SqliteDeviceRepository(DeviceRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(
        self, name: str | None, location: str | None, owner_user_id: UUID | None
    ) -> Device:
        now = datetime.now(UTC).isoformat()
        device_id = uuid4()
        await self._conn.execute(
            """
            INSERT INTO devices (
                id, name, location, owner_user_id, claimed_at, is_active, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(device_id),
                name,
                location,
                str(owner_user_id) if owner_user_id else None,
                now if owner_user_id else None,
                1,
                now,
                now,
            ),
        )
        await self._conn.commit()

        return Device(
            id=device_id,
            name=name,
            location=location,
            owner_user_id=owner_user_id,
            claimed_at=datetime.fromisoformat(now) if owner_user_id else None,
            is_active=True,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    async def get(self, device_id: UUID) -> Device | None:
        cursor = await self._conn.execute(
            (
                "SELECT id, name, location, owner_user_id, claimed_at, is_active, "
                "created_at, updated_at FROM devices WHERE id = ?"
            ),
            (str(device_id),),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return _row_to_device(row)

    async def list(self) -> list[Device]:
        cursor = await self._conn.execute(
            "SELECT id, name, location, owner_user_id, claimed_at, is_active, created_at, updated_at "
            "FROM devices ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_device(r) for r in rows]

    async def update(self, device: Device) -> Device:
        await self._conn.execute(
            """
            UPDATE devices
            SET name = ?, location = ?, owner_user_id = ?, claimed_at = ?, is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                device.name,
                device.location,
                str(device.owner_user_id) if device.owner_user_id else None,
                device.claimed_at.isoformat() if device.claimed_at else None,
                1 if device.is_active else 0,
                device.updated_at.isoformat(),
                str(device.id),
            ),
        )
        await self._conn.commit()
        return device

    async def list_by_ids(self, device_ids: list[UUID]) -> list[Device]:
        if not device_ids:
            return []
        placeholders = ",".join(["?"] * len(device_ids))
        params = [str(d) for d in device_ids]
        cursor = await self._conn.execute(
            f"""
            SELECT id, name, location, owner_user_id, claimed_at, is_active, created_at, updated_at
            FROM devices
            WHERE id IN ({placeholders})
            ORDER BY created_at DESC
            """,
            params,
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_device(r) for r in rows]

    async def list_for_owner(self, owner_user_id: UUID) -> list[Device]:
        cursor = await self._conn.execute(
            """
            SELECT id, name, location, owner_user_id, claimed_at, is_active, created_at, updated_at
            FROM devices
            WHERE owner_user_id = ?
            ORDER BY created_at DESC
            """,
            (str(owner_user_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_device(r) for r in rows]


class SqliteReadingRepository(ReadingRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, reading: Reading) -> Reading:
        await self._conn.execute(
            """
            INSERT INTO readings (
                device_id,
                temperature_c,
                raw_ph_voltage,
                raw_tds_voltage,
                ph_value,
                tds_ppm,
                ph_calibrated,
                received_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(reading.device_id),
                reading.temperature_c,
                reading.raw_ph_voltage,
                reading.raw_tds_voltage,
                reading.ph_value,
                reading.tds_ppm,
                1 if reading.ph_calibrated else 0,
                reading.received_at.isoformat(),
            ),
        )
        await self._conn.commit()
        return reading

    async def list(self) -> list[Reading]:
        cursor = await self._conn.execute("""
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            ORDER BY received_at DESC
            """)
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows]

    async def list_for_device(self, device_id: UUID) -> list[Reading]:
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            WHERE device_id = ?
            ORDER BY received_at DESC
            """,
            (str(device_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows]

    async def list_for_devices(self, device_ids: list[UUID]) -> list[Reading]:
        if not device_ids:
            return []
        placeholders = ",".join(["?"] * len(device_ids))
        params = [str(d) for d in device_ids]
        cursor = await self._conn.execute(
            f"""
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            WHERE device_id IN ({placeholders})
            ORDER BY received_at DESC
            """,
            params,
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows]

    async def list_paginated(self, *, page: int, page_size: int) -> tuple[list[Reading], int]:
        cursor = await self._conn.execute("SELECT COUNT(*) FROM readings")
        (total,) = await cursor.fetchone()
        await cursor.close()

        offset = (page - 1) * page_size
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            ORDER BY received_at DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows], total

    async def list_for_device_filtered(
        self,
        *,
        device_id: UUID,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> list[Reading]:
        clauses = ["device_id = ?"]
        params = [str(device_id)]
        if from_dt is not None:
            clauses.append("received_at >= ?")
            params.append(from_dt.isoformat())
        if to_dt is not None:
            clauses.append("received_at <= ?")
            params.append(to_dt.isoformat())
        where_sql = " AND ".join(clauses)
        cursor = await self._conn.execute(
            f"""
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            WHERE {where_sql}
            ORDER BY received_at DESC
            """,
            params,
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows]

    async def list_for_device_paginated_filtered(
        self,
        *,
        device_id: UUID,
        page: int,
        page_size: int,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> tuple[list[Reading], int]:
        clauses = ["device_id = ?"]
        params = [str(device_id)]
        if from_dt is not None:
            clauses.append("received_at >= ?")
            params.append(from_dt.isoformat())
        if to_dt is not None:
            clauses.append("received_at <= ?")
            params.append(to_dt.isoformat())
        where_sql = " AND ".join(clauses)

        cursor = await self._conn.execute(
            f"SELECT COUNT(*) FROM readings WHERE {where_sql}",
            params,
        )
        (total,) = await cursor.fetchone()
        await cursor.close()

        offset = (page - 1) * page_size
        cursor = await self._conn.execute(
            f"""
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            WHERE {where_sql}
            ORDER BY received_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows], total

    async def list_for_device_paginated(
        self, *, device_id: UUID, page: int, page_size: int
    ) -> tuple[list[Reading], int]:
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM readings WHERE device_id = ?", (str(device_id),)
        )
        (total,) = await cursor.fetchone()
        await cursor.close()

        offset = (page - 1) * page_size
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            WHERE device_id = ?
            ORDER BY received_at DESC
            LIMIT ? OFFSET ?
            """,
            (str(device_id), page_size, offset),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_reading(r) for r in rows], total

    async def get_latest(self, device_id: UUID) -> Reading | None:
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, temperature_c, raw_ph_voltage, raw_tds_voltage,
                   ph_value, tds_ppm, ph_calibrated, received_at
            FROM readings
            WHERE device_id = ?
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (str(device_id),),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return _row_to_reading(row)


def _row_to_ph_calibration(row: tuple[Any, ...]) -> PhCalibrationPoint:
    return PhCalibrationPoint(
        device_id=UUID(row[1]),
        ph_point=row[2],
        voltage=row[3],
        created_at=datetime.fromisoformat(row[4]),
        is_active=bool(row[5]),
    )


class SqlitePhCalibrationRepository(PhCalibrationRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create_point(
        self, device_id: UUID, ph_point: float, voltage: float, *, is_active: bool
    ) -> PhCalibrationPoint:
        created_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            """
            INSERT INTO device_ph_calibrations (
                device_id, ph_point, voltage, created_at, is_active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(device_id), ph_point, voltage, created_at, 1 if is_active else 0),
        )
        await self._conn.commit()
        return PhCalibrationPoint(
            device_id=device_id,
            ph_point=ph_point,
            voltage=voltage,
            created_at=datetime.fromisoformat(created_at),
            is_active=is_active,
        )

    async def list_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]:
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, ph_point, voltage, created_at, is_active
            FROM device_ph_calibrations
            WHERE device_id = ?
            ORDER BY created_at DESC
            """,
            (str(device_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_ph_calibration(r) for r in rows]

    async def list_active_points_for_device(self, device_id: UUID) -> list[PhCalibrationPoint]:
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, ph_point, voltage, created_at, is_active
            FROM device_ph_calibrations
            WHERE device_id = ? AND is_active = 1
            ORDER BY created_at DESC
            """,
            (str(device_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_ph_calibration(r) for r in rows]

    async def list_latest_inactive_points_for_device(
        self, device_id: UUID
    ) -> list[PhCalibrationPoint]:
        cursor = await self._conn.execute(
            """
            SELECT id, device_id, ph_point, voltage, created_at, is_active
            FROM device_ph_calibrations
            WHERE id IN (
                SELECT MAX(id)
                FROM device_ph_calibrations
                WHERE device_id = ? AND is_active = 0
                GROUP BY ph_point
            )
            """,
            (str(device_id),),
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [_row_to_ph_calibration(r) for r in rows]

    async def deactivate_active_points(self, device_id: UUID) -> None:
        await self._conn.execute(
            """
            UPDATE device_ph_calibrations
            SET is_active = 0
            WHERE device_id = ? AND is_active = 1
            """,
            (str(device_id),),
        )
        await self._conn.commit()

    async def activate_points(self, device_id: UUID, points: list[PhCalibrationPoint]) -> None:
        if not points:
            return
        created_at_values = [p.created_at.isoformat() for p in points]
        placeholders = ",".join(["?"] * len(created_at_values))
        await self._conn.execute(
            f"""
            UPDATE device_ph_calibrations
            SET is_active = 1
            WHERE device_id = ? AND created_at IN ({placeholders})
            """,
            [str(device_id), *created_at_values],
        )
        await self._conn.commit()


class SqliteDeviceApiKeyRepository(DeviceApiKeyRepository):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, device_id: UUID, key_hash: str) -> None:
        created_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            """
            INSERT INTO device_api_keys (device_id, key_hash, created_at, revoked_at)
            VALUES (?, ?, ?, NULL)
            """,
            (str(device_id), key_hash, created_at),
        )
        await self._conn.commit()

    async def get_device_id_for_key(self, key_hash: str) -> UUID | None:
        cursor = await self._conn.execute(
            """
            SELECT device_id
            FROM device_api_keys
            WHERE key_hash = ? AND revoked_at IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (key_hash,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return UUID(row[0])

    async def revoke(self, device_id: UUID, key_hash: str) -> None:
        revoked_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            """
            UPDATE device_api_keys
            SET revoked_at = ?
            WHERE device_id = ? AND key_hash = ? AND revoked_at IS NULL
            """,
            (revoked_at, str(device_id), key_hash),
        )
        await self._conn.commit()
