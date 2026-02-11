from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.jwt_utils import decode_jwt


@dataclass(slots=True)
class UserContext:
    user_id: UUID
    actor_user_id: UUID
    email: str | None
    role: str

    @property
    def is_demo(self) -> bool:
        return self.role == "demo"


async def jwt_dependency(
    authorization: str | None = Header(default=None, convert_underscores=False),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_jwt(token)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc


def get_user_context_from_claims(claims: dict) -> UserContext:
    settings = get_settings()
    role = str(claims.get("role") or "owner").lower()
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        actor_id = UUID(sub)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if role == "demo":
        view_user_id = claims.get("view_user_id")
        if not view_user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        try:
            user_id = UUID(view_user_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
        if settings.single_owner_mode and settings.owner_user_id:
            if settings.owner_user_id.strip() != str(user_id):
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return UserContext(
            user_id=user_id,
            actor_user_id=actor_id,
            email=claims.get("email"),
            role="demo",
        )

    if settings.single_owner_mode:
        owner_email = settings.owner_email.strip()
        owner_user_id = settings.owner_user_id.strip()
        if not owner_email and not owner_user_id:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Owner not configured",
            )
        if owner_email:
            claim_email = claims.get("email")
            if not claim_email or claim_email.lower() != owner_email.lower():
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if owner_user_id:
            if owner_user_id != str(actor_id):
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return UserContext(
        user_id=actor_id,
        actor_user_id=actor_id,
        email=claims.get("email"),
        role="owner",
    )


def get_user_id_from_claims(claims: dict) -> UUID:
    return get_user_context_from_claims(claims).user_id


async def user_context_dependency(
    request: Request,
    claims: dict = Depends(jwt_dependency),
) -> UserContext:
    ctx = get_user_context_from_claims(claims)
    user_service = getattr(request.app.state, "user_service", None)
    if user_service is not None:
        user = await user_service.get_user(ctx.user_id)
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return ctx


async def require_write_access(
    ctx: UserContext = Depends(user_context_dependency),
) -> UserContext:
    if ctx.is_demo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Demo account is read-only")
    return ctx


def require_auth_dependency(auth_enabled: bool):
    if auth_enabled:
        return Depends(jwt_dependency)
    return Depends(lambda: None)


async def device_api_key_dependency(
    request: Request,
    authorization: str | None = Header(default=None, convert_underscores=False),
) -> UUID:
    """
    Validate device API key and return the device_id (string UUID).
    Actual verification is delegated to a service stored on app.state.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing device API key")

    api_key = authorization.removeprefix("Bearer ").strip()
    service = getattr(request.app.state, "device_api_key_service", None)
    if service is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Device auth not configured"
        )

    device_id = await service.resolve_device_id(api_key)
    if device_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid device API key")

    return device_id
