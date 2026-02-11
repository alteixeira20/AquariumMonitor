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
  cat <<'EOF' > apps/simulator/config.toml
[backend]
base_url = "http://localhost:8000"
owner_email = ""
owner_password = ""
demo_email = "demo"
demo_password = "demo"
wait_for_setup = true
auto_setup = false
poll_seconds = 3

[simulator]
tick_seconds = 10
seed = 42
state_path = "./state/sim_state.json"
queue_path = "../backend/data/sim_queue.jsonl"
queue_poll_seconds = 2
EOF
  echo "Created apps/simulator/config.toml for UI-driven simulations."
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
