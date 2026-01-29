from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.aquariums import router as aquariums_router
from app.api.v1.devices import router as devices_router
from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.login import router as login_router
from app.api.v1.setup import router as setup_router
from app.api.v1.readings import router as readings_router
from app.core.auth import jwt_dependency

# Root API Router
api_router = APIRouter()

# Versioned sub-routers
api_router.include_router(health_router, prefix="/v1", tags=["health"])
api_router.include_router(login_router, prefix="/v1", tags=["auth"])
api_router.include_router(setup_router, prefix="/v1", tags=["auth"])
api_router.include_router(events_router, prefix="/v1", tags=["events"])
api_router.include_router(
    aquariums_router,
    prefix="/v1/aquariums",
    tags=["aquariums"],
    dependencies=[Depends(jwt_dependency)],
)
api_router.include_router(
    devices_router,
    prefix="/v1/devices",
    tags=["devices"],
    dependencies=[Depends(jwt_dependency)],
)
api_router.include_router(
    readings_router,
    prefix="/v1/readings",
    tags=["readings"],
)
