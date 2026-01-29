from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CalibrationPointCreateRequest(BaseModel):
    ph_point: float = Field(..., description="Calibration pH point (4.01, 6.86, 9.18)")
    voltage: float = Field(..., description="Measured voltage for the calibration point")


class CalibrationPointResponse(BaseModel):
    ph_point: float
    voltage: float
    created_at: datetime
    is_active: bool
