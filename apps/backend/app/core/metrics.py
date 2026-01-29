from __future__ import annotations

from collections import defaultdict
from threading import Lock
from time import time


_lock = Lock()
_requests_total: dict[tuple[str, str, str], int] = defaultdict(int)
_readings_created_total = 0
_devices_created_total = 0
_process_start_time = time()


def inc_request(method: str, path: str, status_code: int | None) -> None:
    status = str(status_code) if status_code is not None else "0"
    key = (method, path, status)
    with _lock:
        _requests_total[key] += 1


def inc_readings_created() -> None:
    global _readings_created_total
    with _lock:
        _readings_created_total += 1


def inc_devices_created() -> None:
    global _devices_created_total
    with _lock:
        _devices_created_total += 1


def render_prometheus() -> str:
    with _lock:
        lines = [
            "# HELP app_requests_total Total HTTP requests by method, path, status",
            "# TYPE app_requests_total counter",
        ]
        for (method, path, status), value in _requests_total.items():
            lines.append(
                'app_requests_total{method="%(method)s",path="%(path)s",status="%(status)s"} %(value)d'
                % {"method": method, "path": path, "status": status, "value": value}
            )
        lines.extend(
            [
                "# HELP app_readings_created_total Total readings created",
                "# TYPE app_readings_created_total counter",
                f"app_readings_created_total {_readings_created_total}",
                "# HELP app_devices_created_total Total devices created",
                "# TYPE app_devices_created_total counter",
                f"app_devices_created_total {_devices_created_total}",
                "# HELP app_process_uptime_seconds Process uptime in seconds",
                "# TYPE app_process_uptime_seconds gauge",
                f"app_process_uptime_seconds {int(time() - _process_start_time)}",
            ]
        )
        return "\n".join(lines) + "\n"
