"""add wind_speed to predictions and indexes

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("predictions", sa.Column("wind_speed", sa.Float(), nullable=True))

    op.create_index("ix_predictions_risk_level", "predictions", ["risk_level"])
    op.create_index("ix_predictions_lat_lon",    "predictions", ["lat", "lon"])
    op.create_index("ix_weather_snapshots_lat_lon",    "weather_snapshots", ["lat", "lon"])
    op.create_index("ix_weather_snapshots_fetched_at", "weather_snapshots", ["fetched_at"])


def downgrade() -> None:
    op.drop_column("predictions", "wind_speed")
    op.drop_index("ix_predictions_risk_level",          table_name="predictions")
    op.drop_index("ix_predictions_lat_lon",             table_name="predictions")
    op.drop_index("ix_weather_snapshots_lat_lon",       table_name="weather_snapshots")
    op.drop_index("ix_weather_snapshots_fetched_at",    table_name="weather_snapshots")
