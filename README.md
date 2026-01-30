<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python badge">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI badge">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite badge">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker badge">
</p>

<h1 align="center">AquariumMonitor</h1>
<p align="center">Open-source, self-hosted aquarium monitoring system with real-time metrics, device simulation, and a clean API for DIY builders.</p>
<p align="center"><sub><em>Single-owner by design, demo-ready for showcases, built to be extended with custom hardware.</em></sub></p>

## Table of Contents
1. [At a Glance](#at-a-glance)
2. [About](#about)
3. [Documentation](#documentation)
4. [Scope](#scope)
5. [Roadmap](#roadmap)
6. [License](#license)

## At a Glance
- Open-source aquarium monitoring system built for self-hosted deployments.
- Real-time telemetry ingestion with strict validation and calibration gates.
- SQLite default with MariaDB optional for heavier workloads.
- Stats and time-series endpoints designed for live dashboards.
- Demo access is optional and read-only for safe public previews.

## About
AquariumMonitor targets DIY aquarists who want a reliable, self-hosted monitoring stack that can grow from a single tank to multi-device setups. The backend prioritizes correctness and clarity so it stays approachable for peers who want to learn or extend it.

## Documentation
- [Docs hub](docs/README.md)
- [Architecture](docs/architecture.md)
- [Backend overview](docs/backend/README.md)
- [Self-hosting guide](docs/self_hosting.md)
- [Simulator](docs/simulator.md)
- [Frontend overview](docs/frontend/README.md)

## Quickstart (self-hosted)
```
cp apps/backend/.env.example apps/backend/.env
make prod
```

Add the simulator:
```
make prod-sim
```

## Scope
- Backend API for aquariums, devices, calibration, and readings
- Device simulator for live demo data
- Web dashboard for real-time and historical views
- DIY device guide (planned)

## Roadmap
- Backend migration with clean history
- Simulator and seeded demo data
- Dashboard UI (Next.js)
- Full DIY hardware tutorial

## License
[CC BY-NC 4.0](LICENSE)
