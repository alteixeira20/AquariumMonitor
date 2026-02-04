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

(
  cd apps/simulator
  SIM_CONFIG=./config.toml python3 main.py
) &
pids+=("$!")

wait "${pids[@]}"
