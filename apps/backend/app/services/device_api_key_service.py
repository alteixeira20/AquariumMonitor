from __future__ import annotations

from uuid import UUID

from app.core.security import generate_device_api_key, hash_device_api_key
from app.repositories.base_repository import DeviceApiKeyRepository, DeviceRepository


class DeviceApiKeyService:
    def __init__(
        self,
        device_repo: DeviceRepository,
        api_key_repo: DeviceApiKeyRepository,
    ) -> None:
        self.device_repo = device_repo
        self.api_key_repo = api_key_repo

    async def create_key(self, device_id: UUID) -> str:
        device = await self.device_repo.get(device_id)
        if device is None:
            raise ValueError("Device not found")

        api_key = generate_device_api_key()
        key_hash = hash_device_api_key(api_key)
        await self.api_key_repo.create(device_id, key_hash)
        return api_key

    async def resolve_device_id(self, api_key: str) -> UUID | None:
        key_hash = hash_device_api_key(api_key)
        return await self.api_key_repo.get_device_id_for_key(key_hash)

    async def revoke_key(self, device_id: UUID, api_key: str) -> None:
        key_hash = hash_device_api_key(api_key)
        resolved = await self.api_key_repo.get_device_id_for_key(key_hash)
        if resolved is None or resolved != device_id:
            raise ValueError("API key not found")
        await self.api_key_repo.revoke(device_id, key_hash)
