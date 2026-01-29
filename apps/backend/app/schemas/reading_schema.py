from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReadingCreateRequest(BaseModel):
    """
    Raw telemetry sent by the ESP32.
    Backend will compute pH, TDS, and timestamps.
    """

    temperature_c: float = Field(..., description="Temperature in Celsius")
    raw_ph_voltage: float = Field(..., description="Raw voltage from pH sensor")
    raw_tds_voltage: float = Field(..., description="Raw voltage from TDS sensor")


class ReadingResponse(BaseModel):
    """
    Fully processed reading with calibrated values.
    """

    device_id: UUID
    temperature_c: float
    raw_ph_voltage: float
    raw_tds_voltage: float

    ph_value: float
    tds_ppm: float
    ph_calibrated: bool

    received_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadingListResponse(BaseModel):
    """
    Paginated list of readings.
    """

    readings: list[ReadingResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class ReadingSeriesPoint(BaseModel):
    bucket_start: datetime
    temperature_median: float
    ph_median: float
    tds_median: float
    count: int


class ReadingSeriesResponse(BaseModel):
    bucket_seconds: int
    points: list[ReadingSeriesPoint]
