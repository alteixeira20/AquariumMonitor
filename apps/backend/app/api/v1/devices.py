from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import require_service
from app.core.auth import UserContext, require_write_access, user_context_dependency
from app.schemas.calibration_schema import (
    CalibrationPointCreateRequest,
    CalibrationPointResponse,
)
from app.schemas.device_schema import (
    DeviceApiKeyRevokeRequest,
    DeviceApiKeyResponse,
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceStatusResponse,
)
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.device_api_key_service import DeviceApiKeyService
from app.services.device_service import DeviceService
from app.services.ph_calibration_service import PhCalibrationService
from app.services.device_status_service import DeviceStatusService
from app.services.reading_service import ReadingService

router = APIRouter()


def get_device_service(request: Request) -> DeviceService:
    return require_service(request, "device_service", "Device service")


ServiceDep = Annotated[DeviceService, Depends(get_device_service)]


def get_aquarium_device_service(request: Request) -> AquariumDeviceService:
    return require_service(request, "aquarium_device_service", "Aquarium-device service")


def get_device_status_service(request: Request) -> DeviceStatusService:
    return require_service(request, "device_status_service", "Device status service")


def get_device_api_key_service(request: Request) -> DeviceApiKeyService:
    return require_service(request, "device_api_key_service", "Device API keys")


def get_ph_calibration_service(request: Request) -> PhCalibrationService:
    return require_service(request, "ph_calibration_service", "Calibration service")


ApiKeyServiceDep = Annotated[DeviceApiKeyService, Depends(get_device_api_key_service)]
AquariumDeviceServiceDep = Annotated[AquariumDeviceService, Depends(get_aquarium_device_service)]
UserContextDep = Annotated[UserContext, Depends(user_context_dependency)]
WriteAccessDep = Annotated[UserContext, Depends(require_write_access)]
DeviceStatusServiceDep = Annotated[DeviceStatusService, Depends(get_device_status_service)]
CalibrationServiceDep = Annotated[PhCalibrationService, Depends(get_ph_calibration_service)]


def get_reading_service(request: Request) -> ReadingService:
    return require_service(request, "reading_service", "Reading service")


ReadingServiceDep = Annotated[ReadingService, Depends(get_reading_service)]


class _StatsFilters(BaseModel):
    from_dt: datetime | None = Field(None, alias="from")
    to_dt: datetime | None = Field(None, alias="to")

    model_config = ConfigDict(populate_by_name=True)


@router.post("", response_model=DeviceResponse, status_code=201)
async def register_device(
    payload: DeviceRegisterRequest,
    service: ServiceDep,
    ctx: WriteAccessDep,
):
    device = await service.register_device(
        name=payload.name,
        location=payload.location,
        owner_user_id=ctx.user_id,
    )
    return DeviceResponse.from_domain(device)


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    service: ServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
):
    device_ids = await association_service.list_devices_for_user(ctx.user_id)
    devices = await service.list_devices_by_ids(device_ids)
    return [DeviceResponse.from_domain(d) for d in devices]


@router.get("/owned", response_model=list[DeviceResponse])
async def list_owned_devices(
    service: ServiceDep,
    ctx: UserContextDep,
):
    devices = await service.list_devices_for_owner(ctx.user_id)
    return [DeviceResponse.from_domain(d) for d in devices]


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    service: ServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
):
    visible_device_ids = await association_service.list_devices_for_user(ctx.user_id)
    if device_id not in visible_device_ids:
        raise HTTPException(status_code=404, detail="Device not found")
    device = await service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.from_domain(device)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID,
    service: ServiceDep,
    ctx: WriteAccessDep,
) -> None:
    try:
        await service.delete_device(device_id, ctx.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{device_id}/claim", response_model=DeviceResponse, status_code=200)
async def claim_device(
    device_id: UUID,
    service: ServiceDep,
    ctx: WriteAccessDep,
):
    try:
        device = await service.claim_device(device_id, ctx.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DeviceResponse.from_domain(device)


@router.post(
    "/{device_id}/api-keys",
    response_model=DeviceApiKeyResponse,
    status_code=201,
)
async def create_device_api_key(
    device_id: UUID,
    service: ApiKeyServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: WriteAccessDep,
):
    visible_device_ids = await association_service.list_devices_for_user(ctx.user_id)
    if device_id not in visible_device_ids:
        raise HTTPException(status_code=403, detail="Device not visible")
    try:
        api_key = await service.create_key(device_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DeviceApiKeyResponse(device_id=device_id, api_key=api_key)


@router.post("/{device_id}/api-keys/revoke", status_code=204)
async def revoke_device_api_key(
    device_id: UUID,
    payload: DeviceApiKeyRevokeRequest,
    service: ApiKeyServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: WriteAccessDep,
) -> None:
    visible_device_ids = await association_service.list_devices_for_user(ctx.user_id)
    if device_id not in visible_device_ids:
        raise HTTPException(status_code=403, detail="Device not visible")
    try:
        await service.revoke_key(device_id, payload.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(
    device_id: UUID,
    service: DeviceStatusServiceDep,
    ctx: UserContextDep,
) -> DeviceStatusResponse:
    result = await service.get_status(ctx.user_id, device_id)
    return DeviceStatusResponse(**result)


@router.get("/{device_id}/stats", status_code=200)
async def get_device_stats(
    device_id: UUID,
    service: ReadingServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_StatsFilters, Depends()],
) -> dict[str, float]:
    visible_device_ids = await association_service.list_devices_for_user(ctx.user_id)
    if device_id not in visible_device_ids:
        raise HTTPException(status_code=404, detail="Device not found")
    return await service.get_device_stats(
        device_id=device_id, from_dt=filters.from_dt, to_dt=filters.to_dt
    )


@router.post("/{device_id}/calibration/start", status_code=204)
async def start_ph_calibration(
    device_id: UUID,
    service: CalibrationServiceDep,
    ctx: WriteAccessDep,
) -> None:
    await service.start(ctx.user_id, device_id)


@router.post(
    "/{device_id}/calibration/points",
    response_model=CalibrationPointResponse,
    status_code=201,
)
async def add_ph_calibration_point(
    device_id: UUID,
    payload: CalibrationPointCreateRequest,
    service: CalibrationServiceDep,
    ctx: WriteAccessDep,
) -> CalibrationPointResponse:
    point = await service.add_point(ctx.user_id, device_id, payload.ph_point, payload.voltage)
    return CalibrationPointResponse(
        ph_point=point.ph_point,
        voltage=point.voltage,
        created_at=point.created_at,
        is_active=point.is_active,
    )


@router.post(
    "/{device_id}/calibration/activate",
    response_model=list[CalibrationPointResponse],
    status_code=200,
)
async def activate_ph_calibration(
    device_id: UUID,
    service: CalibrationServiceDep,
    ctx: WriteAccessDep,
) -> list[CalibrationPointResponse]:
    points = await service.activate(ctx.user_id, device_id)
    return [
        CalibrationPointResponse(
            ph_point=point.ph_point,
            voltage=point.voltage,
            created_at=point.created_at,
            is_active=True,
        )
        for point in points
    ]


@router.get(
    "/{device_id}/calibration",
    response_model=list[CalibrationPointResponse],
)
async def get_ph_calibration(
    device_id: UUID,
    service: CalibrationServiceDep,
    ctx: UserContextDep,
) -> list[CalibrationPointResponse]:
    points = await service.get_current(ctx.user_id, device_id)
    return [
        CalibrationPointResponse(
            ph_point=point.ph_point,
            voltage=point.voltage,
            created_at=point.created_at,
            is_active=point.is_active,
        )
        for point in points
    ]
