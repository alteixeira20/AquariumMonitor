"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "aquariums",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("water_type", sa.Enum("fresh", "salt", name="water_type"), nullable=False),
        sa.Column("liters", sa.Float(), nullable=False),
        sa.Column("temperature_min", sa.Float(), nullable=False),
        sa.Column("temperature_max", sa.Float(), nullable=False),
        sa.Column("ph_min", sa.Float(), nullable=False),
        sa.Column("ph_max", sa.Float(), nullable=False),
        sa.Column("tds_min", sa.Float(), nullable=False),
        sa.Column("tds_max", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_aquariums_user_id", "aquariums", ["user_id"], unique=False)

    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "readings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False),
        sa.Column("raw_ph_voltage", sa.Float(), nullable=False),
        sa.Column("raw_tds_voltage", sa.Float(), nullable=False),
        sa.Column("ph_value", sa.Float(), nullable=False),
        sa.Column("tds_ppm", sa.Float(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
    )
    op.create_index("ix_readings_device_id", "readings", ["device_id"], unique=False)
    op.create_index("ix_readings_received_at", "readings", ["received_at"], unique=False)

    op.create_table(
        "aquarium_devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("aquarium_id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("attached_at", sa.DateTime(), nullable=False),
        sa.Column("detached_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["aquarium_id"], ["aquariums.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
    )
    op.create_index(
        "ix_aquarium_devices_device_id", "aquarium_devices", ["device_id"], unique=False
    )
    op.create_index(
        "ix_aquarium_devices_aquarium_id", "aquarium_devices", ["aquarium_id"], unique=False
    )

    op.create_table(
        "device_api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
    )
    op.create_index("ix_device_api_keys_device_id", "device_api_keys", ["device_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_device_api_keys_device_id", table_name="device_api_keys")
    op.drop_table("device_api_keys")
    op.drop_index("ix_aquarium_devices_aquarium_id", table_name="aquarium_devices")
    op.drop_index("ix_aquarium_devices_device_id", table_name="aquarium_devices")
    op.drop_table("aquarium_devices")
    op.drop_index("ix_readings_received_at", table_name="readings")
    op.drop_index("ix_readings_device_id", table_name="readings")
    op.drop_table("readings")
    op.drop_table("devices")
    op.drop_index("ix_aquariums_user_id", table_name="aquariums")
    op.drop_table("aquariums")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
