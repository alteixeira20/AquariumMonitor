"""Add aquarium metadata fields

Revision ID: 0004_aquarium_metadata
Revises: 0003_device_owner
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_aquarium_metadata"
down_revision = "0003_device_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "aquariums",
        sa.Column("temperature_enabled", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.add_column(
        "aquariums",
        sa.Column("ph_enabled", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.add_column(
        "aquariums",
        sa.Column("tds_enabled", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.add_column("aquariums", sa.Column("filter_type", sa.String(length=50), nullable=True))
    op.add_column("aquariums", sa.Column("filter_flow_lph", sa.Float(), nullable=True))
    op.add_column("aquariums", sa.Column("heater_watts", sa.Float(), nullable=True))
    op.add_column("aquariums", sa.Column("lighting_type", sa.String(length=50), nullable=True))
    op.add_column("aquariums", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("aquariums", "notes")
    op.drop_column("aquariums", "lighting_type")
    op.drop_column("aquariums", "heater_watts")
    op.drop_column("aquariums", "filter_flow_lph")
    op.drop_column("aquariums", "filter_type")
    op.drop_column("aquariums", "tds_enabled")
    op.drop_column("aquariums", "ph_enabled")
    op.drop_column("aquariums", "temperature_enabled")
