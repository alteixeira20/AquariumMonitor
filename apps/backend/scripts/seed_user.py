from __future__ import annotations

from datetime import datetime
import os
from uuid import uuid4

import asyncio

import aiosqlite
from sqlalchemy import create_engine, text

from app.core.config import Settings
from app.core.backup import resolve_sqlite_path
from app.core.security import hash_password
from app.repositories.sqlite_repository import init_db


def main() -> None:
    email = os.getenv("SEED_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("SEED_ADMIN_PASSWORD", "").strip()
    if not email or not password:
        print("Seed user skipped (SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD not set)")
        return

    settings = Settings(
        _env_file=os.environ.get("ENV_FILE", ".env"),
        _env_file_encoding="utf-8",
    )

    if settings.storage_backend == "sqlite":
        asyncio.run(_seed_sqlite(settings, email, password))
        return

    engine = create_engine(settings.mariadb_sync_url)
    with engine.begin() as conn:
        # Idempotent seed: only inserts if the admin email is not present.
        result = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
        if result.first() is not None:
            print("Seed user already exists")
            return

        conn.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, is_active, created_at)
                VALUES (:id, :email, :password_hash, :is_active, :created_at)
                """
            ),
            {
                "id": str(uuid4()),
                "email": email,
                "password_hash": hash_password(password),
                "is_active": True,
                "created_at": datetime.utcnow(),
            },
        )
        print("Seed user created")


async def _seed_sqlite(settings: Settings, email: str, password: str) -> None:
    db_path = resolve_sqlite_path(settings.database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(
        str(db_path), timeout=settings.sqlite_busy_timeout_ms / 1000
    )
    await init_db(
        str(db_path),
        conn,
        journal_mode=settings.sqlite_journal_mode,
        synchronous=settings.sqlite_synchronous,
        busy_timeout_ms=settings.sqlite_busy_timeout_ms,
    )
    cursor = await conn.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = await cursor.fetchone()
    await cursor.close()
    if row is not None:
        print("Seed user already exists")
        await conn.close()
        return

    await conn.execute(
        """
        INSERT INTO users (id, email, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            email,
            hash_password(password),
            1,
            datetime.utcnow().isoformat(),
        ),
    )
    await conn.commit()
    await conn.close()
    print("Seed user created")


if __name__ == "__main__":
    main()
