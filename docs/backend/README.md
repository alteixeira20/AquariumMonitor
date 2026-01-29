# Backend overview

The backend is the source of truth for aquariums, devices, calibration, and readings. It is designed for a single owner, with an optional demo user that can view data but cannot modify it.

## Key responsibilities
- User setup and authentication
- Aquarium and device management
- Calibration enforcement
- Reading ingestion and validation
- Stats and time‑series aggregation

## Core endpoints
- Setup and login: [API reference](api.md)
- Devices, aquariums, and readings: [API reference](api.md)
- Configuration: [Configuration](configuration.md)
- Storage & backups: [Storage](storage.md)
- Operations: [Runbook](runbook.md)
- Testing: [Testing](testing.md)

## First‑run setup
The first‑run flow creates the owner account. If demo access is enabled in configuration, the UI can offer a demo login option. The demo account is read‑only and intended for showcasing the dashboard.
