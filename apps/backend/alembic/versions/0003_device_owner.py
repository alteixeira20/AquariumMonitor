"""add device ownership

Revision ID: 0003_device_owner
Revises: 0002_ph_calibration
Create Date: 2026-01-28

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_device_owner"
down_revision = "0002_ph_calibration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("owner_user_id", sa.String(length=36), nullable=True))
    op.add_column("devices", sa.Column("claimed_at", sa.DateTime(), nullable=True))
    op.create_index("ix_devices_owner_user_id", "devices", ["owner_user_id"], unique=False)
    op.create_foreign_key(
        "fk_devices_owner_user_id",
        "devices",
        "users",
        ["owner_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_devices_owner_user_id", "devices", type_="foreignkey")
    op.drop_index("ix_devices_owner_user_id", table_name="devices")
    op.drop_column("devices", "claimed_at")
    op.drop_column("devices", "owner_user_id")
