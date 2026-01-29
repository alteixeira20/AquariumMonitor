#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}
ADMIN_EMAIL=${ADMIN_EMAIL:-}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-}

user_auth_header=()
if [[ -n "$ADMIN_EMAIL" && -n "$ADMIN_PASSWORD" ]]; then
  echo "==> Setup status"
  setup_status=$(curl -s "${BASE_URL}/v1/setup/status")
  echo "$setup_status" | jq .
  configured=$(echo "$setup_status" | jq -r '.configured')

  if [[ "$configured" == "false" ]]; then
    echo "==> Running first-time setup"
    setup_resp=$(curl -s -X POST "${BASE_URL}/v1/setup" -H "Content-Type: application/json" -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")
    echo "$setup_resp" | jq .
  fi

  echo "==> Login"
  login_resp=$(curl -s -X POST "${BASE_URL}/v1/login" -H "Content-Type: application/json" -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")
  echo "$login_resp" | jq .
  jwt=$(echo "$login_resp" | jq -r '.access_token')
  user_auth_header=(-H "Authorization: Bearer ${jwt}")
fi

if [[ ${#user_auth_header[@]} -eq 0 ]]; then
  echo "Missing ADMIN_EMAIL/ADMIN_PASSWORD; user endpoints will fail."
fi

echo "==> Health"
curl -s "${BASE_URL}/v1/health" | jq .

echo "==> Readiness"
curl -s "${BASE_URL}/v1/readiness" | jq .

echo "==> Register device"
device_resp=$(curl -s -X POST "${BASE_URL}/v1/devices" -H "Content-Type: application/json" "${user_auth_header[@]}" -d '{"name":"Manual","location":"CLI"}')
echo "$device_resp" | jq .
device_id=$(echo "$device_resp" | jq -r '.id')

if [[ -n "$device_id" && "$device_id" != "null" ]]; then
  if [[ ${#user_auth_header[@]} -gt 0 ]]; then
    echo "==> Create aquarium"
    aquarium_resp=$(curl -s -X POST "${BASE_URL}/v1/aquariums" -H "Content-Type: application/json" "${user_auth_header[@]}" -d '{"name":"Main Tank","water_type":"fresh","liters":120,"temperature_min":22,"temperature_max":26,"ph_min":6.5,"ph_max":7.5,"tds_min":150,"tds_max":350}')
    echo "$aquarium_resp" | jq .
    aquarium_id=$(echo "$aquarium_resp" | jq -r '.id')

    echo "==> Add calibration points"
    curl -s -X POST "${BASE_URL}/v1/devices/${device_id}/calibration/points" -H "Content-Type: application/json" "${user_auth_header[@]}" -d '{"ph_point":4.01,"voltage":3.0}' | jq .
    curl -s -X POST "${BASE_URL}/v1/devices/${device_id}/calibration/points" -H "Content-Type: application/json" "${user_auth_header[@]}" -d '{"ph_point":6.86,"voltage":2.5}' | jq .
    curl -s -X POST "${BASE_URL}/v1/devices/${device_id}/calibration/points" -H "Content-Type: application/json" "${user_auth_header[@]}" -d '{"ph_point":9.18,"voltage":2.0}' | jq .
    curl -s -X POST "${BASE_URL}/v1/devices/${device_id}/calibration/activate" "${user_auth_header[@]}" | jq .

    echo "==> Attach device"
    curl -s -X POST "${BASE_URL}/v1/aquariums/${aquarium_id}/devices/${device_id}" "${user_auth_header[@]}"

    echo "==> List aquarium devices"
    curl -s "${BASE_URL}/v1/aquariums/${aquarium_id}/devices" "${user_auth_header[@]}" | jq .

    echo "==> Device status"
    curl -s "${BASE_URL}/v1/devices/${device_id}/status" "${user_auth_header[@]}" | jq .

    echo "==> Create device API key"
    key_resp=$(curl -s -X POST "${BASE_URL}/v1/devices/${device_id}/api-keys" "${user_auth_header[@]}")
    echo "$key_resp" | jq .
    device_api_key=$(echo "$key_resp" | jq -r '.api_key')

    echo "==> Create reading"
    curl -s -X POST "${BASE_URL}/v1/readings/${device_id}" -H "Content-Type: application/json" -H "Authorization: Bearer ${device_api_key}" -d '{"temperature_c":25,"raw_ph_voltage":2.3,"raw_tds_voltage":1.0}' | jq .

    echo "==> List readings (last 24h)"
    from_ts=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
    curl -s "${BASE_URL}/v1/readings/${device_id}?from=${from_ts}" "${user_auth_header[@]}" | jq .
  fi
fi

echo "==> Metrics"
curl -s "${BASE_URL}/v1/metrics" | jq .
