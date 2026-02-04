# Simulator

The simulator generates realistic aquarium telemetry through the API. It is designed for demos and testing without physical hardware.

## How it works
1) Waits for the backend to be ready
2) Checks setup status
3) Logs in as the owner
4) Provisions aquariums, devices, calibration, and attachments
5) Streams readings on a fixed interval

## Configuration
Copy the example config:
```
cp config.example.toml config.toml
```

Key options:
- `backend.base_url`
- `backend.owner_email` / `backend.owner_password`
- `simulator.tick_seconds`
- `simulator.seed`
- `simulator.state_path`
- `simulator.queue_path` / `simulator.queue_poll_seconds`
- `aquariums` and `devices` with patterns

## UI-triggered simulations
The backend exposes:
```
POST /v1/simulator/devices
```
This appends a JSONL record into the simulator queue. The simulator watches the queue and begins streaming readings for that device.

If you only use UI-triggered simulations, owner credentials are optional. Provide
`backend.owner_email` / `backend.owner_password` only if you want the simulator to
provision aquariums and devices from the TOML config.

## Run locally
```
SIM_CONFIG=./config.toml python main.py
```
For UI‑triggered simulations, point the queue path at the backend data folder:
```
# config.toml
queue_path = "../backend/data/sim_queue.jsonl"
```

## Docker
Use the compose profile:
```
docker compose -f infra/docker-compose.sqlite.yml --profile simulator up -d
```
