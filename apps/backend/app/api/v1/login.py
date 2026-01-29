from __future__ import annotations

from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import require_service
from app.core.config import get_settings
from app.core.jwt_utils import create_jwt
from app.schemas.auth_schema import LoginRequest, LoginResponse
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(request: Request) -> UserService:
    return require_service(request, "user_service", "User service")


ServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest, service: ServiceDep) -> LoginResponse:
    if (await service.count_users()) == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Setup required")

    settings = get_settings()
    if settings.demo_enabled and (
        payload.email.strip().lower() == settings.demo_username.strip().lower()
    ):
        if payload.password != settings.demo_password:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        owner = await service.get_primary_user()
        if owner is None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Owner account not initialized")
        try:
            demo_user_id = UUID(settings.demo_user_id)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Demo user not configured"
            ) from exc
        token = create_jwt(
            {
                "sub": str(demo_user_id),
                "email": payload.email,
                "role": "demo",
                "view_user_id": str(owner.id),
            }
        )
        return LoginResponse(access_token=token, token_type="bearer")

    user = await service.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_jwt({"sub": str(user.id), "email": user.email, "role": "owner"})
    return LoginResponse(access_token=token, token_type="bearer")
