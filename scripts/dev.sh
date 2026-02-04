#!/usr/bin/env bash

set -euo pipefail

pids=()

cleanup() {
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}

trap cleanup EXIT INT TERM

make -C apps/backend dev &
pids+=("$!")

make -C apps/frontend dev &
pids+=("$!")

if [[ ! -f apps/simulator/config.toml ]]; then
  cp apps/simulator/config.example.toml apps/simulator/config.toml
  echo "Created apps/simulator/config.toml from example for dev."
fi

if [[ ! -d apps/simulator/.venv ]]; then
  python3 -m venv apps/simulator/.venv
  apps/simulator/.venv/bin/pip install --upgrade pip
  apps/simulator/.venv/bin/pip install -r apps/simulator/requirements.txt
fi

(
  cd apps/simulator
  SIM_CONFIG=./config.toml ./.venv/bin/python3 main.py
) &
pids+=("$!")

wait "${pids[@]}"
