# API reference

Base URL: `/v1`

## Auth & setup
- `GET /setup/status` — returns whether the owner exists and whether demo is enabled.
- `POST /setup` — creates the owner account on first run.
- `GET /me` — returns the authenticated user context.
- `POST /login` — returns a JWT for the owner or demo account.

`POST /setup` request:
```json
{ "email": "owner@example.com", "password": "change-me" }
```

`POST /login` response:
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Notes:
- If the instance is not configured, `/login` returns `409`.
- Demo login is optional and read‑only when enabled via configuration.

## Aquariums
- `POST /aquariums` — create aquarium.
- `GET /aquariums` — list aquariums for current user.
- `GET /aquariums/{aquarium_id}` — get aquarium.
- `PUT /aquariums/{aquarium_id}` — update aquarium.
- `DELETE /aquariums/{aquarium_id}` — delete aquarium.
- `POST /aquariums/{aquarium_id}/devices/{device_id}` — attach device.
- `DELETE /aquariums/{aquarium_id}/devices/{device_id}` — detach device.
- `GET /aquariums/{aquarium_id}/devices` — list attached devices.
- `GET /aquariums/{aquarium_id}/stats` — medians across attached devices.
- `GET /aquariums/{aquarium_id}/devices/{device_id}/stats` — medians for a device within the aquarium.

## Devices
- `POST /devices` — register device.
- `GET /devices` — list devices attached to your aquariums.
- `GET /devices/owned` — list devices you own (including unattached).
- `GET /devices/{device_id}` — get device.
- `DELETE /devices/{device_id}` — delete device.
- `POST /devices/{device_id}/claim` — claim an unowned device.
- `POST /devices/{device_id}/api-keys` — generate device API key.
- `POST /devices/{device_id}/api-keys/revoke` — revoke device API key.
- `GET /devices/{device_id}/status` — online/offline based on last reading.
- `GET /devices/{device_id}/stats` — medians for a device.

### pH calibration
Calibration is required before attachment and readings.
- `POST /devices/{device_id}/calibration/start`
- `POST /devices/{device_id}/calibration/points`
- `POST /devices/{device_id}/calibration/activate`
- `GET /devices/{device_id}/calibration`

Point payload:
```json
{ "ph_point": 6.86, "voltage": 2.48 }
```

## Readings
- `POST /readings/{device_id}` — submit a reading (device API key required).
- `GET /readings/{device_id}` — list readings (JWT required).
- `GET /readings/{device_id}/paginated` — list readings with pagination.
- `GET /readings/{device_id}/latest` — most recent reading.
- `GET /readings/{device_id}/series` — time‑series buckets for charts.

Reading payload:
```json
{
  "temperature_c": 25.2,
  "raw_ph_voltage": 2.48,
  "raw_tds_voltage": 1.0
}
```

## Alerts
- `GET /alerts` — list alerts (JWT required).

Filters (query params):
- `aquarium_id` — filter by aquarium.
- `alert_type` — `sensor_out_of_range`, `device_offline`, `sensor_missing_data`.
- `sensor` — `temperature`, `ph`, `tds`.
- `level` — 0..3.
- `unresolved_only` — defaults to `true`.
- `page` / `page_size`.

## Health & metrics
- `GET /health` — liveness check.
- `GET /readiness` — storage readiness.
- `GET /metrics` — lightweight internal counters.
- `GET /metrics/prometheus` — Prometheus exposition.

## Simulator
- `POST /simulator/devices` — enqueue a simulated device stream.
  - Creates calibration points, issues a device API key, and attaches the device before enqueueing.

Request body:
```json
{
  "device_id": "uuid",
  "aquarium_id": "uuid",
  "preset_id": "reef-drift"
}
```
