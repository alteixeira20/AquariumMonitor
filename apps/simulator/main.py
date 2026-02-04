from __future__ import annotations

import json
import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import tomllib

PH_POINTS = (4.01, 6.86, 9.18)
TDS_VREF = 2.3
PH_VREF = 5.0

PRESET_TO_PATTERN = {
    "reef-drift": "all_three_mix",
    "fresh-sunrise": "temp_daily_cycle",
    "nano-stable": "temp_ph_mix",
    "salt-pulse": "tds_rise",
    "planted-cycle": "ph_drift_down",
    "cichlid-rush": "ph_drift_up",
    "brackish-tide": "tds_rise",
    "tropical-rain": "temp_spike",
    "desert-oasis": "temp_daily_cycle",
    "stress-test": "all_three_mix",
}


@dataclass
class BackendConfig:
    base_url: str
    owner_email: str
    owner_password: str
    wait_for_setup: bool
    auto_setup: bool
    poll_seconds: int


@dataclass
class SimulatorConfig:
    tick_seconds: int
    seed: int
    state_path: Path
    queue_path: Path
    queue_poll_seconds: int


@dataclass
class CalibrationConfig:
    ph4_voltage: float
    ph7_voltage: float
    ph9_voltage: float


@dataclass
class DeviceConfig:
    name: str
    pattern: str


@dataclass
class AquariumConfig:
    name: str
    water_type: str
    liters: float
    temperature_min: float
    temperature_max: float
    ph_min: float
    ph_max: float
    tds_min: float
    tds_max: float
    devices: list[DeviceConfig]


@dataclass
class AppConfig:
    backend: BackendConfig
    simulator: SimulatorConfig
    calibration: CalibrationConfig
    aquariums: list[AquariumConfig]


@dataclass
class DeviceState:
    device_id: str
    api_key: str
    pattern: str
    aquarium: AquariumConfig
    phase: float = 0.0
    drift: float = 0.0
    event_until: float = 0.0


class SimulatorState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {
            "aquariums": {},
            "devices": {},
            "device_ids": {},
            "active_devices": [],
            "queue_offset": 0,
        }
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get_aquarium_id(self, name: str) -> str | None:
        return self.data.get("aquariums", {}).get(name, {}).get("id")

    def set_aquarium_id(self, name: str, aquarium_id: str) -> None:
        self.data.setdefault("aquariums", {})[name] = {"id": aquarium_id}
        self.save()

    def get_device(self, name: str) -> dict[str, str] | None:
        return self.data.get("devices", {}).get(name)

    def set_device(self, name: str, device_id: str, api_key: str) -> None:
        self.data.setdefault("devices", {})[name] = {
            "id": device_id,
            "api_key": api_key,
        }
        self.save()

    def get_device_by_id(self, device_id: str) -> dict[str, str] | None:
        return self.data.get("device_ids", {}).get(device_id)

    def set_device_by_id(self, device_id: str, api_key: str) -> None:
        self.data.setdefault("device_ids", {})[device_id] = {
            "api_key": api_key,
        }
        self.save()

    def get_queue_offset(self) -> int:
        return int(self.data.get("queue_offset", 0) or 0)

    def set_queue_offset(self, offset: int) -> None:
        self.data["queue_offset"] = offset
        self.save()

    def get_active_devices(self) -> list[dict[str, Any]]:
        return list(self.data.get("active_devices", []))

    def add_active_device(
        self, device_id: str, aquarium_id: str, pattern: str
    ) -> None:
        active = self.data.setdefault("active_devices", [])
        if any(item.get("device_id") == device_id for item in active):
            return
        active.append(
            {
                "device_id": device_id,
                "aquarium_id": aquarium_id,
                "pattern": pattern,
            }
        )
        self.save()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def load_config(path: Path) -> AppConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    backend = data.get("backend", {})
    simulator = data.get("simulator", {})
    calibration = data.get("calibration", {})

    aquariums: list[AquariumConfig] = []
    for item in data.get("aquariums", []):
        devices = [DeviceConfig(**d) for d in item.get("devices", [])]
        aquariums.append(AquariumConfig(**{**item, "devices": devices}))

    cfg = AppConfig(
        backend=BackendConfig(
            base_url=os.getenv("SIM_BACKEND_URL", backend.get("base_url", "http://localhost:8000")),
            owner_email=os.getenv("SIM_OWNER_EMAIL", backend.get("owner_email", "")),
            owner_password=os.getenv("SIM_OWNER_PASSWORD", backend.get("owner_password", "")),
            wait_for_setup=_env_bool("SIM_WAIT_FOR_SETUP", backend.get("wait_for_setup", True)),
            auto_setup=_env_bool("SIM_AUTO_SETUP", backend.get("auto_setup", False)),
            poll_seconds=int(os.getenv("SIM_POLL_SECONDS", backend.get("poll_seconds", 3))),
        ),
        simulator=SimulatorConfig(
            tick_seconds=int(os.getenv("SIM_TICK_SECONDS", simulator.get("tick_seconds", 5))),
            seed=int(os.getenv("SIM_SEED", simulator.get("seed", 42))),
            state_path=Path(
                os.getenv("SIM_STATE_PATH", simulator.get("state_path", "./data/sim_state.json"))
            ),
            queue_path=Path(
                os.getenv("SIM_QUEUE_PATH", simulator.get("queue_path", "./data/sim_queue.jsonl"))
            ),
            queue_poll_seconds=int(
                os.getenv("SIM_QUEUE_POLL_SECONDS", simulator.get("queue_poll_seconds", 2))
            ),
        ),
        calibration=CalibrationConfig(
            ph4_voltage=float(calibration.get("ph4_voltage", 3.0)),
            ph7_voltage=float(calibration.get("ph7_voltage", 2.5)),
            ph9_voltage=float(calibration.get("ph9_voltage", 2.0)),
        ),
        aquariums=aquariums,
    )

    if not cfg.backend.owner_email or not cfg.backend.owner_password:
        raise SystemExit("Owner email/password not configured for simulator.")

    if not cfg.aquariums:
        raise SystemExit("No aquariums defined in simulator config.")

    return cfg


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=10.0)
        self.token: str | None = None

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def wait_for_ready(self, poll_seconds: int) -> None:
        while True:
            try:
                resp = self.client.get(f"{self.base_url}/v1/readiness")
                if resp.status_code == 200:
                    return
            except httpx.RequestError:
                pass
            time.sleep(poll_seconds)

    def setup_status(self) -> dict[str, Any]:
        resp = self.client.get(f"{self.base_url}/v1/setup/status")
        resp.raise_for_status()
        return resp.json()

    def setup_owner(self, email: str, password: str) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/setup",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()

    def login(self, email: str, password: str) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/login",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        self.token = resp.json()["access_token"]

    def list_aquariums(self) -> list[dict[str, Any]]:
        resp = self.client.get(f"{self.base_url}/v1/aquariums", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def create_aquarium(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self.client.post(
            f"{self.base_url}/v1/aquariums", headers=self._headers(), json=payload
        )
        resp.raise_for_status()
        return resp.json()

    def list_owned_devices(self) -> list[dict[str, Any]]:
        resp = self.client.get(
            f"{self.base_url}/v1/devices/owned", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def create_device(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self.client.post(
            f"{self.base_url}/v1/devices", headers=self._headers(), json=payload
        )
        resp.raise_for_status()
        return resp.json()

    def create_device_key(self, device_id: str) -> dict[str, Any]:
        resp = self.client.post(
            f"{self.base_url}/v1/devices/{device_id}/api-keys",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_aquarium(self, aquarium_id: str) -> dict[str, Any]:
        resp = self.client.get(
            f"{self.base_url}/v1/aquariums/{aquarium_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def get_device(self, device_id: str) -> dict[str, Any]:
        resp = self.client.get(
            f"{self.base_url}/v1/devices/{device_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def get_calibration(self, device_id: str) -> list[dict[str, Any]]:
        resp = self.client.get(
            f"{self.base_url}/v1/devices/{device_id}/calibration",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def start_calibration(self, device_id: str) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/devices/{device_id}/calibration/start",
            headers=self._headers(),
        )
        if resp.status_code not in {200, 204}:
            resp.raise_for_status()

    def add_calibration_point(self, device_id: str, ph_point: float, voltage: float) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/devices/{device_id}/calibration/points",
            headers=self._headers(),
            json={"ph_point": ph_point, "voltage": voltage},
        )
        resp.raise_for_status()

    def activate_calibration(self, device_id: str) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/devices/{device_id}/calibration/activate",
            headers=self._headers(),
        )
        resp.raise_for_status()

    def attach_device(self, aquarium_id: str, device_id: str) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/aquariums/{aquarium_id}/devices/{device_id}",
            headers=self._headers(),
        )
        if resp.status_code not in {200, 204, 409}:
            resp.raise_for_status()

    def post_reading(self, device_id: str, api_key: str, payload: dict[str, Any]) -> None:
        resp = self.client.post(
            f"{self.base_url}/v1/readings/{device_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()


def ensure_setup(client: ApiClient, cfg: BackendConfig) -> None:
    while True:
        status = client.setup_status()
        if status.get("configured"):
            return
        if cfg.auto_setup:
            client.setup_owner(cfg.owner_email, cfg.owner_password)
            return
        if not cfg.wait_for_setup:
            raise SystemExit("Backend not configured. Run setup in the UI first.")
        time.sleep(cfg.poll_seconds)


def _find_by_name(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("name") == name:
            return item
    return None


def _aquarium_from_response(payload: dict[str, Any]) -> AquariumConfig:
    return AquariumConfig(
        name=payload["name"],
        water_type=payload["water_type"],
        liters=float(payload["liters"]),
        temperature_min=float(payload["temperature_min"]),
        temperature_max=float(payload["temperature_max"]),
        ph_min=float(payload["ph_min"]),
        ph_max=float(payload["ph_max"]),
        tds_min=float(payload["tds_min"]),
        tds_max=float(payload["tds_max"]),
        devices=[],
    )


def _calibration_points(cfg: CalibrationConfig) -> dict[float, float]:
    return {
        4.01: cfg.ph4_voltage,
        6.86: cfg.ph7_voltage,
        9.18: cfg.ph9_voltage,
    }


def _is_calibrated(points: list[dict[str, Any]]) -> bool:
    active = [p for p in points if p.get("is_active")]
    if len(active) != 3:
        return False
    values = {round(float(p["ph_point"]), 2) for p in active}
    return values == {4.01, 6.86, 9.18}


def _ph_to_voltage(target_ph: float, calibration: dict[float, float]) -> float:
    points = sorted(calibration.items(), key=lambda item: item[0])
    if target_ph <= points[0][0]:
        return points[0][1]
    if target_ph >= points[-1][0]:
        return points[-1][1]
    for idx in range(len(points) - 1):
        p1, v1 = points[idx]
        p2, v2 = points[idx + 1]
        if p1 <= target_ph <= p2:
            if p2 == p1:
                return v1
            ratio = (target_ph - p1) / (p2 - p1)
            return v1 + ratio * (v2 - v1)
    return points[1][1]


def _tds_from_voltage(temp_c: float, voltage: float) -> float:
    compensation_coeff = 1.0 + 0.02 * (temp_c - 25.0)
    compensation_voltage = voltage / compensation_coeff
    tds = (
        133.42 * compensation_voltage**3
        - 255.86 * compensation_voltage**2
        + 857.39 * compensation_voltage
    ) * 0.5
    return max(tds, 0.0)


def _voltage_for_tds(temp_c: float, target_tds: float) -> float:
    low, high = 0.0, TDS_VREF
    for _ in range(30):
        mid = (low + high) / 2.0
        tds = _tds_from_voltage(temp_c, mid)
        if tds < target_tds:
            low = mid
        else:
            high = mid
    return max(0.0, min(TDS_VREF, (low + high) / 2.0))


def _clamp(value: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, value))


def _noise(rand: random.Random, amplitude: float) -> float:
    return rand.uniform(-amplitude, amplitude)


def _pattern_values(
    pattern: str,
    device_state: DeviceState,
    tick: int,
    aquarium: AquariumConfig,
    rand: random.Random,
) -> tuple[float, float, float]:
    temp_base = (aquarium.temperature_min + aquarium.temperature_max) / 2.0
    ph_base = (aquarium.ph_min + aquarium.ph_max) / 2.0
    tds_base = (aquarium.tds_min + aquarium.tds_max) / 2.0

    temp = temp_base
    ph = ph_base
    tds = tds_base

    if pattern == "temp_daily_cycle":
        period = 24 * 60 * 60
        phase = (tick * 5) % period
        temp = temp_base + 1.5 * math.sin(2 * math.pi * phase / period)
    elif pattern == "temp_spike":
        if device_state.event_until <= time.time() and rand.random() < 0.01:
            device_state.event_until = time.time() + 120
        temp = temp_base + (3.5 if device_state.event_until > time.time() else 0.0)
    elif pattern == "ph_drift_up":
        device_state.drift += 0.003
        ph = ph_base + device_state.drift
    elif pattern == "ph_drift_down":
        device_state.drift -= 0.003
        ph = ph_base + device_state.drift
    elif pattern == "ph_crash":
        if device_state.event_until <= time.time() and rand.random() < 0.005:
            device_state.event_until = time.time() + 180
        ph = ph_base - (1.0 if device_state.event_until > time.time() else 0.0)
    elif pattern == "tds_rise":
        device_state.drift += 0.8
        tds = tds_base + device_state.drift
    elif pattern == "tds_drop":
        if device_state.event_until <= time.time() and rand.random() < 0.01:
            device_state.event_until = time.time() + 120
        tds = tds_base - (60 if device_state.event_until > time.time() else 0.0)
    elif pattern == "temp_ph_mix":
        period = 12 * 60 * 60
        phase = (tick * 5) % period
        temp = temp_base + 1.0 * math.sin(2 * math.pi * phase / period)
        device_state.drift += 0.002
        ph = ph_base + device_state.drift
    elif pattern == "ph_tds_mix":
        device_state.drift -= 0.002
        ph = ph_base + device_state.drift
        tds = tds_base + (tick % 200) * 0.6
    elif pattern == "temp_tds_mix":
        period = 18 * 60 * 60
        phase = (tick * 5) % period
        temp = temp_base + 1.2 * math.sin(2 * math.pi * phase / period)
        tds = tds_base + (tick % 150) * 0.5
    elif pattern == "all_three_mix":
        period = 24 * 60 * 60
        phase = (tick * 5) % period
        temp = temp_base + 1.0 * math.sin(2 * math.pi * phase / period)
        ph = ph_base + 0.2 * math.sin(2 * math.pi * phase / (period / 2))
        tds = tds_base + 40 * math.sin(2 * math.pi * phase / (period / 3))

    temp += _noise(rand, 0.2)
    ph += _noise(rand, 0.03)
    tds += _noise(rand, 5.0)

    temp = _clamp(temp, aquarium.temperature_min - 2, aquarium.temperature_max + 2)
    ph = _clamp(ph, aquarium.ph_min - 0.6, aquarium.ph_max + 0.6)
    tds = _clamp(tds, aquarium.tds_min - 80, aquarium.tds_max + 80)

    return temp, ph, tds


def provision(client: ApiClient, cfg: AppConfig, state: SimulatorState) -> dict[str, DeviceState]:
    aquariums = client.list_aquariums()
    devices = client.list_owned_devices()

    calibration = _calibration_points(cfg.calibration)
    device_states: dict[str, DeviceState] = {}

    for aquarium_cfg in cfg.aquariums:
        existing_aquarium = _find_by_name(aquariums, aquarium_cfg.name)
        if existing_aquarium is None:
            created = client.create_aquarium(
                {
                    "name": aquarium_cfg.name,
                    "water_type": aquarium_cfg.water_type,
                    "liters": aquarium_cfg.liters,
                    "temperature_min": aquarium_cfg.temperature_min,
                    "temperature_max": aquarium_cfg.temperature_max,
                    "ph_min": aquarium_cfg.ph_min,
                    "ph_max": aquarium_cfg.ph_max,
                    "tds_min": aquarium_cfg.tds_min,
                    "tds_max": aquarium_cfg.tds_max,
                }
            )
            aquarium_id = created["id"]
        else:
            aquarium_id = existing_aquarium["id"]
        state.set_aquarium_id(aquarium_cfg.name, aquarium_id)

        for device_cfg in aquarium_cfg.devices:
            existing_device = _find_by_name(devices, device_cfg.name)
            device_id: str
            api_key: str

            if existing_device is None:
                created_device = client.create_device(
                    {"name": device_cfg.name, "location": "simulator"}
                )
                device_id = created_device["id"]
            else:
                device_id = existing_device["id"]

            points = client.get_calibration(device_id)
            if not _is_calibrated(points):
                client.start_calibration(device_id)
                for ph_point, voltage in calibration.items():
                    client.add_calibration_point(device_id, ph_point, voltage)
                client.activate_calibration(device_id)

            client.attach_device(aquarium_id, device_id)

            cached = state.get_device(device_cfg.name)
            if cached and cached.get("id") == device_id and cached.get("api_key"):
                api_key = cached["api_key"]
            else:
                key_resp = client.create_device_key(device_id)
                api_key = key_resp["api_key"]
                state.set_device(device_cfg.name, device_id, api_key)

            device_states[device_id] = DeviceState(
                device_id=device_id,
                api_key=api_key,
                pattern=device_cfg.pattern,
                aquarium=aquarium_cfg,
            )

    return device_states


def _ensure_device_state(
    client: ApiClient,
    cfg: AppConfig,
    state: SimulatorState,
    device_states: dict[str, DeviceState],
    aquarium_id: str,
    device_id: str,
    pattern: str,
) -> None:
    if device_id in device_states:
        return

    aquarium_payload = client.get_aquarium(aquarium_id)
    aquarium_cfg = _aquarium_from_response(aquarium_payload)

    client.get_device(device_id)

    points = client.get_calibration(device_id)
    if not _is_calibrated(points):
        calibration = _calibration_points(cfg.calibration)
        client.start_calibration(device_id)
        for ph_point, voltage in calibration.items():
            client.add_calibration_point(device_id, ph_point, voltage)
        client.activate_calibration(device_id)

    client.attach_device(aquarium_id, device_id)

    cached = state.get_device_by_id(device_id)
    if cached and cached.get("api_key"):
        api_key = cached["api_key"]
    else:
        key_resp = client.create_device_key(device_id)
        api_key = key_resp["api_key"]
        state.set_device_by_id(device_id, api_key)

    device_states[device_id] = DeviceState(
        device_id=device_id,
        api_key=api_key,
        pattern=pattern,
        aquarium=aquarium_cfg,
    )


def load_active_devices(
    client: ApiClient,
    cfg: AppConfig,
    state: SimulatorState,
    device_states: dict[str, DeviceState],
) -> None:
    for item in state.get_active_devices():
        device_id = str(item.get("device_id", "")).strip()
        aquarium_id = str(item.get("aquarium_id", "")).strip()
        pattern = str(item.get("pattern", "all_three_mix")).strip()
        if not device_id or not aquarium_id:
            continue
        try:
            _ensure_device_state(
                client, cfg, state, device_states, aquarium_id, device_id, pattern
            )
        except Exception:
            continue


def consume_queue(
    client: ApiClient,
    cfg: AppConfig,
    state: SimulatorState,
    device_states: dict[str, DeviceState],
) -> None:
    queue_path = cfg.simulator.queue_path
    if not queue_path.exists():
        return

    offset = state.get_queue_offset()
    with queue_path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        lines = handle.readlines()
        new_offset = handle.tell()

    if new_offset != offset:
        state.set_queue_offset(new_offset)

    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        device_id = str(payload.get("device_id", "")).strip()
        aquarium_id = str(payload.get("aquarium_id", "")).strip()
        preset_id = str(payload.get("preset_id", "")).strip()
        if not device_id or not aquarium_id:
            continue
        if device_id in device_states:
            continue

        pattern = PRESET_TO_PATTERN.get(preset_id, "all_three_mix")
        try:
            _ensure_device_state(
                client, cfg, state, device_states, aquarium_id, device_id, pattern
            )
            state.add_active_device(device_id, aquarium_id, pattern)
        except Exception:
            continue


def emit_loop(
    client: ApiClient,
    cfg: AppConfig,
    state: SimulatorState,
    device_states: dict[str, DeviceState],
) -> None:
    rand = random.Random(cfg.simulator.seed)
    calibration = _calibration_points(cfg.calibration)
    tick = 0
    last_queue_check = 0.0

    while True:
        now = time.time()
        if now - last_queue_check >= cfg.simulator.queue_poll_seconds:
            consume_queue(client, cfg, state, device_states)
            last_queue_check = now

        for state in device_states.values():
            temp, ph, tds = _pattern_values(
                state.pattern, state, tick, state.aquarium, rand
            )
            voltage_ph = _ph_to_voltage(ph, calibration)
            voltage_tds = _voltage_for_tds(temp, tds)

            payload = {
                "temperature_c": round(temp, 2),
                "raw_ph_voltage": round(_clamp(voltage_ph, 0.0, PH_VREF), 3),
                "raw_tds_voltage": round(_clamp(voltage_tds, 0.0, TDS_VREF), 3),
            }
            client.post_reading(state.device_id, state.api_key, payload)

        tick += 1
        time.sleep(cfg.simulator.tick_seconds)


def main() -> None:
    config_path = Path(os.getenv("SIM_CONFIG", "./config.toml"))
    if not config_path.exists():
        raise SystemExit(f"Config file not found at {config_path}")

    cfg = load_config(config_path)
    state = SimulatorState(cfg.simulator.state_path)

    client = ApiClient(cfg.backend.base_url)
    client.wait_for_ready(cfg.backend.poll_seconds)
    ensure_setup(client, cfg.backend)
    client.login(cfg.backend.owner_email, cfg.backend.owner_password)

    device_states = provision(client, cfg, state)
    load_active_devices(client, cfg, state, device_states)
    emit_loop(client, cfg, state, device_states)


if __name__ == "__main__":
    main()
