from __future__ import annotations

from uuid import UUID

from app.core.exceptions import DomainError
from app.domain.aquarium import Aquarium
from app.repositories.base_repository import AquariumRepository


class AquariumService:
    def __init__(self, repository: AquariumRepository) -> None:
        self.repository = repository

    async def create_aquarium(self, aquarium: Aquarium) -> Aquarium:
        return await self.repository.create(aquarium)

    async def list_aquariums(self, user_id: UUID) -> list[Aquarium]:
        return await self.repository.list_for_user(user_id)

    async def get_aquarium(self, user_id: UUID, aquarium_id: UUID) -> Aquarium:
        aquarium = await self.repository.get(aquarium_id)
        if aquarium is None or aquarium.user_id != user_id:
            raise DomainError("Aquarium not found", status_code=404, error="not_found")
        return aquarium
