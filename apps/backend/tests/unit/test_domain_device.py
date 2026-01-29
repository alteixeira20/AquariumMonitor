from __future__ import annotations

from datetime import UTC, datetime
from time import sleep

from app.domain.device import Device


def test_device_initializes_correctly():
    d = Device()

    assert d.id is not None
    assert isinstance(d.created_at, datetime)
    assert isinstance(d.updated_at, datetime)
    assert d.created_at.tzinfo is UTC
    assert d.updated_at.tzinfo is UTC
    assert d.is_active is True


def test_device_mark_inactive_updates_timestamp():
    d = Device()
    before = d.updated_at

    sleep(0.001)  # ensure timestamp difference
    d.mark_inactive()

    assert d.is_active is False
    assert d.updated_at > before


def test_device_rename_updates_timestamp():
    d = Device(name="Old")
    before = d.updated_at

    sleep(0.001)
    d.rename("New Name")

    assert d.name == "New Name"
    assert d.updated_at > before


def test_device_move_updates_timestamp():
    d = Device(location="Kitchen")
    before = d.updated_at

    sleep(0.001)
    d.move("Office")

    assert d.location == "Office"
    assert d.updated_at > before


def test_device_touch():
    d = Device()
    before = d.updated_at

    sleep(0.001)
    d.touch()

    assert d.updated_at > before
