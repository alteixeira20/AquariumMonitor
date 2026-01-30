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
- `aquariums` and `devices` with patterns

## Run locally
```
SIM_CONFIG=./config.toml python main.py
```

## Docker
Use the compose profile:
```
docker compose -f infra/docker-compose.sqlite.yml --profile simulator up -d
```
