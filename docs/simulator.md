# Simulator

The simulator is a long‑running process that generates realistic sensor readings through the API. It is intended for demos and local testing when you don’t have physical devices connected.

## What it does
- Waits for backend readiness
- Uses the owner account (write access required)
- Creates aquariums and devices if missing
- Applies pH calibration
- Attaches devices to aquariums
- Sends patterned readings on a schedule

## Configuration (TOML)
Copy the example:
```
cp apps/simulator/config.example.toml apps/simulator/config.toml
```

Key fields:
- `backend.base_url`
- `backend.owner_email` / `backend.owner_password`
- `simulator.tick_seconds`
- `simulator.seed`
- `simulator.state_path`
- `aquariums` and `devices`

## Patterns
Built‑in patterns include:
- `temp_daily_cycle`, `temp_spike`
- `ph_drift_up`, `ph_drift_down`, `ph_crash`
- `tds_rise`, `tds_drop`
- `temp_ph_mix`, `ph_tds_mix`, `temp_tds_mix`, `all_three_mix`

Each pattern adds small noise so values remain natural even when stable.

## Run locally
```
cd apps/simulator
SIM_CONFIG=./config.toml python main.py
```

## Run with Docker
```
docker compose -f infra/docker-compose.sqlite.yml --profile simulator up -d
```

Convenience:
```
make simulator-up
```

The simulator stores state in `SIM_STATE_PATH` so it can reuse device IDs and API keys across restarts.

## End‑to‑end demo checklist
1) Start backend:
```
cp apps/backend/.env.example apps/backend/.env
make prod
```
2) Create owner account:
```
curl -X POST http://localhost:8000/v1/setup \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"change-me"}'
```
3) Start simulator:
```
make simulator-up
```
4) Login and query data:
```
TOKEN=$(curl -s http://localhost:8000/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"change-me"}' | jq -r .access_token)

curl http://localhost:8000/v1/aquariums \
  -H "Authorization: Bearer $TOKEN"
```
