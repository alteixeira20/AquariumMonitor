from __future__ import annotations

from uuid import UUID

from app.core.exceptions import DomainError
from app.core.security import hash_password, verify_password
from app.domain.user import User
from app.repositories.base_repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def authenticate(self, email: str, password: str) -> User | None:
        email = email.strip().lower()
        user = await self.repository.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.repository.get_by_id(user_id)

    async def create_user(self, email: str, password: str) -> User:
        email = email.strip().lower()
        existing = await self.repository.get_by_email(email)
        if existing is not None:
            raise DomainError("User already exists", status_code=409, error="conflict")
        user = User(email=email, password_hash=hash_password(password), is_active=True)
        return await self.repository.create(user)

    async def count_users(self) -> int:
        return await self.repository.count()

    async def get_primary_user(self) -> User | None:
        return await self.repository.get_first_user()
