from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.domain.alert import Alert
from app.repositories.base_repository import AlertRepository


class AlertService:
    def __init__(self, alert_repo: AlertRepository) -> None:
        self._alert_repo = alert_repo

    async def create_alert(
        self,
        *,
        aquarium_id: UUID,
        device_id: UUID | None,
        alert_type: str,
        sensor: str | None,
        level: int,
        message: str,
    ) -> Alert:
        alert = Alert(
            aquarium_id=aquarium_id,
            device_id=device_id,
            alert_type=alert_type,
            sensor=sensor,
            level=level,
            message=message,
        )
        return await self._alert_repo.create(alert)

    async def create_alert_if_new(
        self,
        *,
        aquarium_id: UUID,
        device_id: UUID | None,
        alert_type: str,
        sensor: str | None,
        level: int,
        message: str,
        cooldown_minutes: int = 15,
    ) -> Alert | None:
        latest = await self._alert_repo.get_latest_for_key(
            aquarium_id=aquarium_id,
            device_id=device_id,
            alert_type=alert_type,
            sensor=sensor,
        )
        if latest and latest.resolved_at is None:
            if latest.created_at > datetime.now(UTC) - timedelta(minutes=cooldown_minutes):
                return None
        return await self.create_alert(
            aquarium_id=aquarium_id,
            device_id=device_id,
            alert_type=alert_type,
            sensor=sensor,
            level=level,
            message=message,
        )

    async def list_alerts(
        self,
        *,
        aquarium_id: UUID | None,
        alert_type: str | None,
        sensor: str | None,
        level: int | None,
        unresolved_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Alert], int]:
        return await self._alert_repo.list(
            aquarium_id=aquarium_id,
            alert_type=alert_type,
            sensor=sensor,
            level=level,
            unresolved_only=unresolved_only,
            page=page,
            page_size=page_size,
        )
