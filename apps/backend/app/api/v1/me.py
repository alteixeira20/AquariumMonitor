from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.auth import UserContext, user_context_dependency
from app.schemas.auth_schema import UserMeResponse

router = APIRouter()

UserContextDep = Annotated[UserContext, Depends(user_context_dependency)]


@router.get("/me", response_model=UserMeResponse, status_code=status.HTTP_200_OK)
async def me(ctx: UserContextDep) -> UserMeResponse:
    return UserMeResponse(
        user_id=str(ctx.user_id),
        email=ctx.email,
        role=ctx.role,
        is_demo=ctx.is_demo,
    )
