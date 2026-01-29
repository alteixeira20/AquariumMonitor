from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import UserContext, require_write_access, user_context_dependency
from app.domain.aquarium import Aquarium
from app.schemas.aquarium_schema import AquariumCreateRequest, AquariumResponse
from app.schemas.device_schema import DeviceResponse
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.aquarium_service import AquariumService
from app.services.aquarium_stats_service import AquariumStatsService
from app.services.device_service import DeviceService

router = APIRouter()


def get_aquarium_service(request: Request) -> AquariumService:
    service = getattr(request.app.state, "aquarium_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Aquarium service not configured")
    return service


def get_aquarium_device_service(request: Request) -> AquariumDeviceService:
    service = getattr(request.app.state, "aquarium_device_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Aquarium-device service not configured")
    return service


def get_device_service(request: Request) -> DeviceService:
    return request.app.state.device_service


def get_aquarium_stats_service(request: Request) -> AquariumStatsService:
    service = getattr(request.app.state, "aquarium_stats_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Aquarium stats service not configured")
    return service


AquariumServiceDep = Annotated[AquariumService, Depends(get_aquarium_service)]
AquariumDeviceServiceDep = Annotated[AquariumDeviceService, Depends(get_aquarium_device_service)]
AquariumStatsServiceDep = Annotated[AquariumStatsService, Depends(get_aquarium_stats_service)]
DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]
UserContextDep = Annotated[UserContext, Depends(user_context_dependency)]
WriteAccessDep = Annotated[UserContext, Depends(require_write_access)]

class _StatsFilters(BaseModel):
    from_dt: datetime | None = Field(None, alias="from")
    to_dt: datetime | None = Field(None, alias="to")

    model_config = ConfigDict(populate_by_name=True)


@router.post("", response_model=AquariumResponse, status_code=status.HTTP_201_CREATED)
async def create_aquarium(
    payload: AquariumCreateRequest,
    service: AquariumServiceDep,
    ctx: WriteAccessDep,
) -> AquariumResponse:
    aquarium = Aquarium(
        user_id=ctx.user_id,
        name=payload.name,
        water_type=payload.water_type,
        liters=payload.liters,
        temperature_min=payload.temperature_min,
        temperature_max=payload.temperature_max,
        ph_min=payload.ph_min,
        ph_max=payload.ph_max,
        tds_min=payload.tds_min,
        tds_max=payload.tds_max,
    )
    created = await service.create_aquarium(aquarium)
    return AquariumResponse.from_domain(created)


@router.get("", response_model=list[AquariumResponse])
async def list_aquariums(
    service: AquariumServiceDep,
    ctx: UserContextDep,
) -> list[AquariumResponse]:
    aquariums = await service.list_aquariums(ctx.user_id)
    return [AquariumResponse.from_domain(a) for a in aquariums]


@router.get("/{aquarium_id}", response_model=AquariumResponse)
async def get_aquarium(
    aquarium_id: UUID,
    service: AquariumServiceDep,
    ctx: UserContextDep,
) -> AquariumResponse:
    aquarium = await service.get_aquarium(ctx.user_id, aquarium_id)
    return AquariumResponse.from_domain(aquarium)


@router.post("/{aquarium_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def attach_device(
    aquarium_id: UUID,
    device_id: UUID,
    service: AquariumDeviceServiceDep,
    ctx: WriteAccessDep,
) -> None:
    await service.attach_device(ctx.user_id, aquarium_id, device_id)


@router.delete("/{aquarium_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_device(
    aquarium_id: UUID,
    device_id: UUID,
    service: AquariumDeviceServiceDep,
    ctx: WriteAccessDep,
) -> None:
    await service.detach_device(ctx.user_id, aquarium_id, device_id)


@router.get("/{aquarium_id}/devices", response_model=list[DeviceResponse])
async def list_attached_devices(
    aquarium_id: UUID,
    device_service: DeviceServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
) -> list[DeviceResponse]:
    device_ids = await association_service.list_devices_for_aquarium(
        ctx.user_id, aquarium_id
    )
    devices = await device_service.list_devices_by_ids(device_ids)
    return [DeviceResponse.from_domain(d) for d in devices]


@router.get(
    "/{aquarium_id}/stats",
    status_code=status.HTTP_200_OK,
)
async def get_aquarium_stats(
    aquarium_id: UUID,
    service: AquariumStatsServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_StatsFilters, Depends()],
    device_id: UUID | None = None,
) -> dict[str, float]:
    return await service.get_stats(
        user_id=ctx.user_id,
        aquarium_id=aquarium_id,
        device_id=device_id,
        from_dt=filters.from_dt,
        to_dt=filters.to_dt,
    )


@router.get(
    "/{aquarium_id}/devices/{device_id}/stats",
    status_code=status.HTTP_200_OK,
)
async def get_aquarium_device_stats(
    aquarium_id: UUID,
    device_id: UUID,
    service: AquariumStatsServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_StatsFilters, Depends()],
) -> dict[str, float]:
    return await service.get_stats(
        user_id=ctx.user_id,
        aquarium_id=aquarium_id,
        device_id=device_id,
        from_dt=filters.from_dt,
        to_dt=filters.to_dt,
    )
