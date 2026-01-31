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

wait "${pids[@]}"
