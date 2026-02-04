from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import require_service
from app.core.auth import UserContext, require_write_access
from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.schemas.simulator_schema import SimulatorDeviceRequest
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.aquarium_service import AquariumService
from app.services.device_api_key_service import DeviceApiKeyService
from app.services.device_service import DeviceService
from app.services.ph_calibration_service import PhCalibrationService

router = APIRouter()


def get_aquarium_service(request: Request) -> AquariumService:
    return require_service(request, "aquarium_service", "Aquarium service")


def get_device_service(request: Request) -> DeviceService:
    return require_service(request, "device_service", "Device service")


def get_api_key_service(request: Request) -> DeviceApiKeyService:
    return require_service(request, "device_api_key_service", "Device API keys")


def get_aquarium_device_service(request: Request) -> AquariumDeviceService:
    return require_service(request, "aquarium_device_service", "Aquarium-device service")


def get_calibration_service(request: Request) -> PhCalibrationService:
    return require_service(request, "ph_calibration_service", "Calibration service")


WriteAccessDep = Annotated[UserContext, Depends(require_write_access)]
AquariumServiceDep = Annotated[AquariumService, Depends(get_aquarium_service)]
DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]
ApiKeyServiceDep = Annotated[DeviceApiKeyService, Depends(get_api_key_service)]
AquariumDeviceServiceDep = Annotated[
    AquariumDeviceService, Depends(get_aquarium_device_service)
]
CalibrationServiceDep = Annotated[PhCalibrationService, Depends(get_calibration_service)]


@router.post("/devices", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_simulated_device(
    payload: SimulatorDeviceRequest,
    ctx: WriteAccessDep,
    aquarium_service: AquariumServiceDep,
    device_service: DeviceServiceDep,
    aquarium_device_service: AquariumDeviceServiceDep,
    api_key_service: ApiKeyServiceDep,
    calibration_service: CalibrationServiceDep,
) -> dict[str, str]:
    settings = get_settings()
    queue_path = Path(settings.sim_queue_path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    aquarium = await aquarium_service.get_aquarium(ctx.user_id, payload.aquarium_id)
    device = await device_service.get_device(payload.device_id)
    if device is None or device.owner_user_id != ctx.user_id:
        raise DomainError("Device not found", status_code=404, error="not_found")

    await calibration_service.start(ctx.user_id, payload.device_id)
    await calibration_service.add_point(
        ctx.user_id, payload.device_id, 4.01, settings.sim_ph4_voltage
    )
    await calibration_service.add_point(
        ctx.user_id, payload.device_id, 6.86, settings.sim_ph7_voltage
    )
    await calibration_service.add_point(
        ctx.user_id, payload.device_id, 9.18, settings.sim_ph9_voltage
    )
    await calibration_service.activate(ctx.user_id, payload.device_id)

    try:
        await aquarium_device_service.attach_device(
            ctx.user_id, payload.aquarium_id, payload.device_id
        )
    except DomainError as exc:
        if exc.error == "conflict":
            device_ids = await aquarium_device_service.list_devices_for_aquarium(
                ctx.user_id, payload.aquarium_id
            )
            if payload.device_id not in device_ids:
                raise
        else:
            raise

    api_key = await api_key_service.create_key(payload.device_id)

    record = {
        "device_id": str(payload.device_id),
        "aquarium_id": str(payload.aquarium_id),
        "preset_id": payload.preset_id,
        "api_key": api_key,
        "aquarium": {
            "name": aquarium.name,
            "water_type": aquarium.water_type,
            "liters": aquarium.liters,
            "temperature_min": aquarium.temperature_min,
            "temperature_max": aquarium.temperature_max,
            "ph_min": aquarium.ph_min,
            "ph_max": aquarium.ph_max,
            "tds_min": aquarium.tds_min,
            "tds_max": aquarium.tds_max,
        },
        "requested_by": str(ctx.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record))
        handle.write("\n")

    return {"status": "queued"}
