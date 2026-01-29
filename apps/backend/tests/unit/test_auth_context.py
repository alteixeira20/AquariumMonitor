from __future__ import annotations

from uuid import UUID

from app.core.auth import get_user_context_from_claims


def test_user_context_defaults_to_owner():
    owner_id = UUID("00000000-0000-0000-0000-000000000000")
    ctx = get_user_context_from_claims({"sub": str(owner_id), "email": "owner@test.local"})
    assert ctx.user_id == owner_id
    assert ctx.actor_user_id == owner_id
    assert ctx.role == "owner"
    assert ctx.is_demo is False


def test_user_context_demo_view():
    demo_id = UUID("00000000-0000-0000-0000-000000000001")
    owner_id = UUID("00000000-0000-0000-0000-000000000002")
    ctx = get_user_context_from_claims(
        {
            "sub": str(demo_id),
            "email": "demo@test.local",
            "role": "demo",
            "view_user_id": str(owner_id),
        }
    )
    assert ctx.actor_user_id == demo_id
    assert ctx.user_id == owner_id
    assert ctx.role == "demo"
    assert ctx.is_demo is True
