from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import require_service
from app.core.config import get_settings
from app.core.jwt_utils import create_jwt
from app.schemas.setup_schema import SetupRequest, SetupResponse, SetupStatusResponse
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(request: Request) -> UserService:
    return require_service(request, "user_service", "User service")


ServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/setup/status", response_model=SetupStatusResponse, status_code=status.HTTP_200_OK)
async def setup_status(service: ServiceDep) -> SetupStatusResponse:
    settings = get_settings()
    configured = (await service.count_users()) > 0
    return SetupStatusResponse(configured=configured, demo_enabled=settings.demo_enabled)


@router.post("/setup", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
async def setup(payload: SetupRequest, service: ServiceDep) -> SetupResponse:
    if (await service.count_users()) > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Setup already completed")
    user = await service.create_user(payload.email, payload.password)
    token = create_jwt({"sub": str(user.id), "email": user.email, "role": "owner"})
    return SetupResponse(owner_user_id=user.id, access_token=token)
