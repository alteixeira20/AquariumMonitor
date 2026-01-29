"""add per-device ph calibration

Revision ID: 0002_ph_calibration
Revises: 0001_initial
Create Date: 2025-01-02 00:00:00

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_ph_calibration"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "readings",
        sa.Column("ph_calibrated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "device_ph_calibrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("ph_point", sa.Float(), nullable=False),
        sa.Column("voltage", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
    )
    op.create_index(
        "ix_device_ph_calibrations_device_id",
        "device_ph_calibrations",
        ["device_id"],
        unique=False,
    )
    op.create_index(
        "ix_device_ph_calibrations_is_active",
        "device_ph_calibrations",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_device_ph_calibrations_is_active", table_name="device_ph_calibrations")
    op.drop_index("ix_device_ph_calibrations_device_id", table_name="device_ph_calibrations")
    op.drop_table("device_ph_calibrations")
    op.drop_column("readings", "ph_calibrated")
