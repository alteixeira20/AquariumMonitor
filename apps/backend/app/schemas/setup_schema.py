from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SetupStatusResponse(BaseModel):
    configured: bool
    demo_enabled: bool = Field(default=True)


class SetupRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class SetupResponse(BaseModel):
    owner_user_id: UUID
    access_token: str
    token_type: str = "bearer"
