from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.auth import UserContext, require_write_access
from app.core.config import get_settings
from app.schemas.simulator_schema import SimulatorDeviceRequest

router = APIRouter()

WriteAccessDep = Annotated[UserContext, Depends(require_write_access)]


@router.post("/devices", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_simulated_device(
    payload: SimulatorDeviceRequest,
    ctx: WriteAccessDep,
) -> dict[str, str]:
    settings = get_settings()
    queue_path = Path(settings.sim_queue_path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "device_id": str(payload.device_id),
        "aquarium_id": str(payload.aquarium_id),
        "preset_id": payload.preset_id,
        "requested_by": str(ctx.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record))
        handle.write("\n")

    return {"status": "queued"}
