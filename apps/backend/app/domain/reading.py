from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

# Ignore because Python builds may lack datetime.UTC
# ruff: noqa: UP017

# Calibration & physical constants

# pH physical / logical limits
PH_MIN = 0.0
PH_MAX = 14.0

# pH module analog range (SEN0161 is powered at 5 V)
PH_VREF = 5.0

# 3-point calibration (placeholders except for the mid-point):
# Each tuple is (voltage_in_volts, ph_value)
PH_CAL_LOW_V = 3.00
PH_CAL_LOW_PH = 4.01

PH_CAL_MID_V = 2.48  # ~pH 6.86 according to many examples
PH_CAL_MID_PH = 6.86

PH_CAL_HIGH_V = 1.96
PH_CAL_HIGH_PH = 9.18

# TDS sensor output range from the datasheet (0-2.3 V)
TDS_VREF = 2.3


@dataclass(slots=True)
class Reading:
    """
    Domain entity representing one telemetry reading from a device.

    This contains only business logic and plain Python fields — no ORM, no API.

    A reading always belongs to a specific device. The timestamp is generated
    by the backend when the reading is received, not by the IoT device.
    """

    device_id: UUID

    # Raw sensor values received from ESP32
    temperature_c: float  # °C
    raw_ph_voltage: float  # Volts, 0-5 V from pH module
    raw_tds_voltage: float  # Volts, 0-2.3 V from TDS module

    # Processed/calculated values (backend converts)
    ph_value: float | None = None
    tds_ppm: float | None = None
    ph_calibrated: bool = False

    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Validation helpers
    def _validate_inputs(self) -> None:
        """
        Validate raw inputs to catch obviously invalid data early.

        These are sanity bounds, not hard physic limits — you can adjust later.
        """
        if not -5.0 <= self.temperature_c <= 60.0:
            raise ValueError(f"temperature_c out of expected range: {self.temperature_c:.2f} °C")

        if not 0.0 <= self.raw_ph_voltage <= PH_VREF:
            raise ValueError(
                f"raw_ph_voltage out of expected range: "
                f"{self.raw_ph_voltage:.3f} V (expected 0-{PH_VREF} V)"
            )

        if not 0.0 <= self.raw_tds_voltage <= TDS_VREF:
            raise ValueError(
                f"raw_tds_voltage out of expected range: "
                f"{self.raw_tds_voltage:.3f} V (expected 0-{TDS_VREF} V)"
            )

    # Computation helpers
    def _compute_ph_lagrange(self) -> float:
        """
        Convert raw pH voltage into estimated pH using a 3-point Lagrange
        interpolation based on your calibration buffers (4.01, 6.86, 9.18).

        This is a *template* calibration:
        - mid-point (6.86 pH @ ~2.48 V) matches typical docs
        - low / high points use placeholder voltages you can refine later.
        """
        v = self.raw_ph_voltage

        x1 = PH_CAL_LOW_V
        y1 = PH_CAL_LOW_PH

        x2 = PH_CAL_MID_V
        y2 = PH_CAL_MID_PH

        x3 = PH_CAL_HIGH_V
        y3 = PH_CAL_HIGH_PH

        # Standard 3-point Lagrange polynomial
        l1 = ((v - x2) * (v - x3)) / ((x1 - x2) * (x1 - x3))
        l2 = ((v - x1) * (v - x3)) / ((x2 - x1) * (x2 - x3))
        l3 = ((v - x1) * (v - x2)) / ((x3 - x1) * (x3 - x2))

        ph_estimate = y1 * l1 + y2 * l2 + y3 * l3

        # Clamp to physical pH limits
        if ph_estimate < PH_MIN:
            ph_estimate = PH_MIN
        elif ph_estimate > PH_MAX:
            ph_estimate = PH_MAX

        return ph_estimate

    def _compute_ph_linear(self, calibration_points: list[tuple[float, float]]) -> float:
        v = self.raw_ph_voltage
        points_by_voltage = sorted(
            ((voltage, ph_point) for ph_point, voltage in calibration_points),
            key=lambda pair: pair[0],
        )

        if len(points_by_voltage) < 2:
            return self._compute_ph_lagrange()

        if v <= points_by_voltage[0][0]:
            v1, p1 = points_by_voltage[0]
            v2, p2 = points_by_voltage[1]
        elif v >= points_by_voltage[-1][0]:
            v1, p1 = points_by_voltage[-2]
            v2, p2 = points_by_voltage[-1]
        else:
            v1, p1 = points_by_voltage[0]
            v2, p2 = points_by_voltage[1]
            for idx in range(len(points_by_voltage) - 1):
                low_v, low_p = points_by_voltage[idx]
                high_v, high_p = points_by_voltage[idx + 1]
                if low_v <= v <= high_v:
                    v1, p1 = low_v, low_p
                    v2, p2 = high_v, high_p
                    break

        if v1 == v2:
            ph_estimate = p1
        else:
            ph_estimate = p1 + (v - v1) * (p2 - p1) / (v2 - v1)

        if ph_estimate < PH_MIN:
            ph_estimate = PH_MIN
        elif ph_estimate > PH_MAX:
            ph_estimate = PH_MAX

        return ph_estimate

    def compute_ph(self, calibration_points: list[tuple[float, float]] | None = None) -> None:
        """Compute and store the pH value from raw voltage."""
        self._validate_inputs()
        if calibration_points:
            self.ph_value = self._compute_ph_linear(calibration_points)
            self.ph_calibrated = True
            return
        self.ph_value = self._compute_ph_lagrange()
        self.ph_calibrated = False

    def compute_tds(self) -> None:
        """Convert raw voltage into TDS (ppm)."""
        self._validate_inputs()

        compensation_coeff = 1.0 + 0.02 * (self.temperature_c - 25.0)
        compensation_voltage = self.raw_tds_voltage / compensation_coeff

        # Very simplified scaling (template)
        self.tds_ppm = (
            133.42 * compensation_voltage**3
            - 255.86 * compensation_voltage**2
            + 857.39 * compensation_voltage
        ) * 0.5

        self.tds_ppm = max(self.tds_ppm, 0.0)

    def process(self, calibration_points: list[tuple[float, float]] | None = None) -> None:
        """
        Run all calculations after receiving raw data.

        Call this from the service after constructing the Reading.
        """
        self.compute_ph(calibration_points=calibration_points)
        self.compute_tds()
