from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.reading import Reading


def test_ph_is_clamped_within_bounds():
    """Even extreme voltages must produce a pH between 0 and 14."""
    r = Reading(
        device_id=uuid4(),
        temperature_c=25,
        raw_ph_voltage=0.0,
        raw_tds_voltage=1.0,
    )
    r.process()
    assert 0 <= r.ph_value <= 14

    r = Reading(
        device_id=uuid4(),
        temperature_c=25,
        raw_ph_voltage=5.0,
        raw_tds_voltage=1.0,
    )
    r.process()
    assert 0 <= r.ph_value <= 14


def test_tds_never_negative():
    """The domain guarantees TDS never becomes negative."""
    r = Reading(
        device_id=uuid4(),
        temperature_c=5,
        raw_ph_voltage=2.0,
        raw_tds_voltage=0.01,  # extremely low signal
    )
    r.process()

    assert r.tds_ppm >= 0


def test_invalid_temperature_raises():
    """Temperature outside the domain bounds should cause a ValueError."""
    with pytest.raises(ValueError, match="temperature"):
        Reading(
            device_id=uuid4(),
            temperature_c=99,  # invalid temperature
            raw_ph_voltage=2.48,
            raw_tds_voltage=1.2,
        ).process()


def test_low_temperature_raises():
    """Low temperatures outside bounds should raise a ValueError."""
    with pytest.raises(ValueError, match="temperature"):
        Reading(
            device_id=uuid4(),
            temperature_c=-10,  # below allowed minimum
            raw_ph_voltage=2.48,
            raw_tds_voltage=1.2,
        ).process()


def test_raw_ph_voltage_out_of_range_raises():
    """pH voltage above VREF should raise a ValueError."""
    with pytest.raises(ValueError, match="raw_ph_voltage"):
        Reading(
            device_id=uuid4(),
            temperature_c=25,
            raw_ph_voltage=6.0,  # above sensor range
            raw_tds_voltage=1.0,
        ).process()
