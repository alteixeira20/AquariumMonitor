# Domain concepts

These concepts define how the system models aquarium monitoring data.

## Sensors
- **Temperature (°C)** — primary safety metric.
- **pH** — acidity/alkalinity derived from probe voltage.
- **TDS (ppm)** — dissolved solids derived from conductivity voltage.

## Calibration
- pH calibration uses three reference points: 4.01, 6.86, 9.18.
- Calibration is per‑device and is required before attachment and readings.
- Raw voltages are stored alongside computed values for re‑calibration later.

## Aquariums and devices
- An aquarium can have multiple devices attached at once.
- Devices can exist unclaimed but must be owned before use.
- Device attachment history is preserved for accurate time‑range stats.

## Statistics
- Device stats are computed per device.
- Aquarium stats aggregate across all attached devices.
- Time‑series endpoints allow charts by time window.
