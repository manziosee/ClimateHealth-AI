"""add disease_records, locations, model_metrics tables

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "disease_records",
        sa.Column("id",           sa.Integer(),     primary_key=True),
        sa.Column("disease",      sa.String(50),    nullable=False),
        sa.Column("country_code", sa.String(10),    nullable=False),
        sa.Column("year",         sa.Integer(),     nullable=False),
        sa.Column("cases",        sa.Float(),       nullable=True),
        sa.Column("low",          sa.Float(),       nullable=True),
        sa.Column("high",         sa.Float(),       nullable=True),
        sa.Column("source",       sa.String(50),    server_default="WHO_GHO"),
        sa.Column("fetched_at",   sa.DateTime(),    server_default=sa.func.now()),
    )
    op.create_index("ix_disease_records_disease_country", "disease_records", ["disease", "country_code"])
    op.create_index("ix_disease_records_year",            "disease_records", ["year"])

    op.create_table(
        "locations",
        sa.Column("id",           sa.Integer(),     primary_key=True),
        sa.Column("lat",          sa.Float(),       nullable=False),
        sa.Column("lon",          sa.Float(),       nullable=False),
        sa.Column("city",         sa.String(255),   nullable=True),
        sa.Column("country",      sa.String(255),   nullable=True),
        sa.Column("country_code", sa.String(10),    nullable=True),
        sa.Column("admin1",       sa.String(255),   nullable=True),
        sa.Column("display_name", sa.String(512),   nullable=True),
        sa.Column("cached_at",    sa.DateTime(),    server_default=sa.func.now()),
    )
    op.create_index("ix_locations_lat_lon", "locations", ["lat", "lon"])

    op.create_table(
        "model_metrics",
        sa.Column("id",          sa.Integer(),  primary_key=True),
        sa.Column("disease",     sa.String(50), nullable=False),
        sa.Column("model_type",  sa.String(20), nullable=False),
        sa.Column("mae",         sa.Float(),    nullable=False),
        sa.Column("r2",          sa.Float(),    nullable=False),
        sa.Column("n_samples",   sa.Integer(),  nullable=False),
        sa.Column("n_features",  sa.Integer(),  nullable=False),
        sa.Column("notes",       sa.Text(),     nullable=True),
        sa.Column("trained_at",  sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_model_metrics_disease",    "model_metrics", ["disease"])
    op.create_index("ix_model_metrics_trained_at", "model_metrics", ["trained_at"])


def downgrade() -> None:
    op.drop_table("model_metrics")
    op.drop_table("locations")
    op.drop_table("disease_records")
