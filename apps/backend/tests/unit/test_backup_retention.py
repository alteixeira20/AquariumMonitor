from __future__ import annotations

from datetime import UTC, datetime, timedelta
import os
from pathlib import Path

from app.core.backup import _prune_old_backups, resolve_sqlite_path


def test_resolve_sqlite_path_relative():
    path = resolve_sqlite_path("sqlite:///./data/app.db")
    assert path.as_posix().endswith("data/app.db")


def test_resolve_sqlite_path_absolute():
    path = resolve_sqlite_path("sqlite:////var/lib/app.db")
    assert path.as_posix() == "/var/lib/app.db"


def test_prune_old_backups(tmp_path: Path):
    recent = tmp_path / "app.db.20260101_000000"
    old = tmp_path / "app.db.20250101_000000"
    recent.write_text("recent")
    old.write_text("old")

    old_time = datetime.now(UTC) - timedelta(days=10)
    os.utime(old, (old_time.timestamp(), old_time.timestamp()))

    _prune_old_backups(tmp_path, retention_days=7)

    assert recent.exists()
    assert not old.exists()
