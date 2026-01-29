from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import logging
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import sqlite3

from app.core.config import Settings

logger = logging.getLogger(__name__)


def resolve_sqlite_path(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Not a sqlite database URL")
    raw_path = parsed.path or ""
    if database_url.startswith("sqlite:////"):
        return Path("/" + raw_path.lstrip("/"))
    return Path(raw_path.lstrip("/"))


def _backup_sqlite_sync(db_path: Path, dest_path: Path) -> None:
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(dest_path))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def _iter_backup_files(backup_dir: Path) -> Iterable[Path]:
    return backup_dir.glob("*.db.*")


def _prune_old_backups(backup_dir: Path, retention_days: int) -> None:
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    for path in _iter_backup_files(backup_dir):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        except FileNotFoundError:
            continue
        if mtime < cutoff:
            try:
                path.unlink()
            except FileNotFoundError:
                continue


async def backup_sqlite_once(
    db_path: Path, backup_dir: Path, retention_days: int
) -> Path | None:
    if not db_path.exists():
        logger.warning("SQLite DB not found at %s; skipping backup", db_path)
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    dest_path = backup_dir / f"{db_path.name}.{ts}"
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _backup_sqlite_sync, db_path, dest_path)
    _prune_old_backups(backup_dir, retention_days)
    return dest_path


async def backup_loop(settings: Settings, db_path: Path) -> None:
    interval = max(settings.backup_interval_hours, 1)
    while True:
        try:
            dest = await backup_sqlite_once(
                db_path=db_path,
                backup_dir=Path(settings.backup_dir),
                retention_days=max(settings.backup_retention_days, 1),
            )
            if dest is not None:
                logger.info("SQLite backup written to %s", dest)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("SQLite backup failed: %s", exc)
        await asyncio.sleep(interval * 3600)
