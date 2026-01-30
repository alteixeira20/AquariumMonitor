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
    phase: float = 0.0
    drift: float = 0.0
    event_until: float = 0.0


class SimulatorState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {"aquariums": {}, "devices": {}}
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

            cached = state.get_device(device_cfg.name)
            if cached and cached.get("id") == device_id and cached.get("api_key"):
                api_key = cached["api_key"]
            else:
                key_resp = client.create_device_key(device_id)
                api_key = key_resp["api_key"]
                state.set_device(device_cfg.name, device_id, api_key)

            points = client.get_calibration(device_id)
            if not _is_calibrated(points):
                client.start_calibration(device_id)
                for ph_point, voltage in calibration.items():
                    client.add_calibration_point(device_id, ph_point, voltage)
                client.activate_calibration(device_id)

            client.attach_device(aquarium_id, device_id)

            device_states[device_cfg.name] = DeviceState(
                device_id=device_id,
                api_key=api_key,
                pattern=device_cfg.pattern,
            )

    return device_states


def emit_loop(
    client: ApiClient,
    cfg: AppConfig,
    device_states: dict[str, DeviceState],
) -> None:
    rand = random.Random(cfg.simulator.seed)
    calibration = _calibration_points(cfg.calibration)
    tick = 0

    aquarium_lookup = {aq.name: aq for aq in cfg.aquariums}

    while True:
        for aquarium in cfg.aquariums:
            for device_cfg in aquarium.devices:
                state = device_states[device_cfg.name]
                temp, ph, tds = _pattern_values(
                    state.pattern, state, tick, aquarium, rand
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
    emit_loop(client, cfg, device_states)


if __name__ == "__main__":
    main()
