from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import require_service
from app.core.auth import UserContext, device_api_key_dependency, user_context_dependency
from app.schemas.reading_schema import (
    ReadingCreateRequest,
    ReadingListResponse,
    ReadingResponse,
    ReadingSeriesResponse,
)
from app.services.aquarium_device_service import AquariumDeviceService
from app.services.reading_service import ReadingService


def get_reading_service(request: Request) -> ReadingService:
    return require_service(request, "reading_service", "Reading service")


def get_aquarium_device_service(request: Request) -> AquariumDeviceService:
    return require_service(request, "aquarium_device_service", "Aquarium-device service")


ServiceDep = Annotated[ReadingService, Depends(get_reading_service)]
AquariumDeviceServiceDep = Annotated[AquariumDeviceService, Depends(get_aquarium_device_service)]
UserContextDep = Annotated[UserContext, Depends(user_context_dependency)]
DeviceKeyDep = Annotated[UUID, Depends(device_api_key_dependency)]

router = APIRouter()


class _ReadingFilters(BaseModel):
    from_dt: datetime | None = Field(None, alias="from")
    to_dt: datetime | None = Field(None, alias="to")

    model_config = ConfigDict(populate_by_name=True)


class _ReadingPaginationFilters(_ReadingFilters):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class _ReadingSeriesFilters(_ReadingFilters):
    bucket_seconds: int = Field(60, ge=10, le=86400)


async def _assert_device_visible(
    association_service: AquariumDeviceServiceDep,
    ctx: UserContext,
    device_id: UUID,
) -> None:
    device_ids = await association_service.list_devices_for_user(ctx.user_id)
    if device_id not in device_ids:
        raise HTTPException(status_code=404, detail="Device not found")


# ------------------------------------------------------------
# LATEST READING (place BEFORE /{device_id})
# ------------------------------------------------------------
@router.get(
    "/{device_id}/latest",
    response_model=ReadingResponse,
    summary="Get the latest reading for a device",
)
async def get_latest_reading(
    device_id: UUID,
    service: ServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
):
    await _assert_device_visible(association_service, ctx, device_id)
    reading = await service.get_latest_reading(device_id)
    if reading is None:
        raise HTTPException(404, f"No readings found for device {device_id}")
    return reading


# ------------------------------------------------------------
# PAGINATED LIST (also BEFORE /{device_id})
# ------------------------------------------------------------
@router.get(
    "/{device_id}/paginated",
    response_model=ReadingListResponse,
    summary="List readings (paginated)",
)
async def list_readings_for_device_paginated(
    device_id: UUID,
    service: ServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_ReadingPaginationFilters, Depends()],
):
    await _assert_device_visible(association_service, ctx, device_id)
    readings, total = await service.list_readings_for_device_paginated(
        device_id=device_id,
        page=filters.page,
        page_size=filters.page_size,
        from_dt=filters.from_dt,
        to_dt=filters.to_dt,
    )

    return ReadingListResponse(
        readings=readings,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        has_next=(filters.page * filters.page_size < total),
    )


# ------------------------------------------------------------
# SERIES (bucketed)
# ------------------------------------------------------------
@router.get(
    "/{device_id}/series",
    response_model=ReadingSeriesResponse,
    summary="Bucketed time-series for a device",
)
async def list_readings_series(
    device_id: UUID,
    service: ServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_ReadingSeriesFilters, Depends()],
):
    await _assert_device_visible(association_service, ctx, device_id)
    points = await service.get_series(
        device_id=device_id,
        from_dt=filters.from_dt,
        to_dt=filters.to_dt,
        bucket_seconds=filters.bucket_seconds,
    )
    return ReadingSeriesResponse(bucket_seconds=filters.bucket_seconds, points=points)


# ------------------------------------------------------------
# CREATE READING
# ------------------------------------------------------------
@router.post(
    "/{device_id}",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reading(
    device_id: UUID,
    payload: ReadingCreateRequest,
    service: ServiceDep,
    device_key_device_id: DeviceKeyDep,
):
    if device_id != device_key_device_id:
        raise HTTPException(status_code=403, detail="Device API key does not match device")
    try:
        return await service.create_reading(
            device_id=device_id,
            temperature_c=payload.temperature_c,
            raw_ph_voltage=payload.raw_ph_voltage,
            raw_tds_voltage=payload.raw_tds_voltage,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc


# ------------------------------------------------------------
# SIMPLE LIST (placed LAST to avoid capturing all routes)
# ------------------------------------------------------------
@router.get(
    "/{device_id}",
    response_model=list[ReadingResponse],
    summary="List all readings for a device (simple)",
)
async def list_readings_for_device_simple(
    device_id: UUID,
    service: ServiceDep,
    association_service: AquariumDeviceServiceDep,
    ctx: UserContextDep,
    filters: Annotated[_ReadingFilters, Depends()],
):
    await _assert_device_visible(association_service, ctx, device_id)
    return await service.list_readings_for_device(
        device_id, from_dt=filters.from_dt, to_dt=filters.to_dt
    )
