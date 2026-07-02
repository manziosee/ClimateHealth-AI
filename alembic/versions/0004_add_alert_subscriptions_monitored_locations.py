"""add alert_subscriptions and monitored_locations tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-04 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_subscriptions",
        sa.Column("id",               sa.Integer(),     primary_key=True),
        sa.Column("lat",              sa.Float(),       nullable=False),
        sa.Column("lon",              sa.Float(),       nullable=False),
        sa.Column("location_name",    sa.String(255),   nullable=True),
        sa.Column("disease",          sa.String(50),    nullable=False),
        sa.Column("threshold",        sa.String(20),    server_default="High"),
        sa.Column("notify_email",     sa.String(255),   nullable=True),
        sa.Column("notify_phone",     sa.String(50),    nullable=True),
        sa.Column("active",           sa.Boolean(),     server_default=sa.true()),
        sa.Column("last_notified_at", sa.DateTime(),    nullable=True),
        sa.Column("created_at",       sa.DateTime(),    server_default=sa.func.now()),
    )
    op.create_index("ix_alert_subscriptions_disease", "alert_subscriptions", ["disease"])
    op.create_index("ix_alert_subscriptions_active",  "alert_subscriptions", ["active"])

    op.create_table(
        "monitored_locations",
        sa.Column("id",            sa.Integer(),    primary_key=True),
        sa.Column("group_name",    sa.String(100),  nullable=False),
        sa.Column("lat",           sa.Float(),      nullable=False),
        sa.Column("lon",           sa.Float(),      nullable=False),
        sa.Column("location_name", sa.String(255),  nullable=True),
        sa.Column("added_at",      sa.DateTime(),   server_default=sa.func.now()),
    )
    op.create_index("ix_monitored_locations_group", "monitored_locations", ["group_name"])


def downgrade() -> None:
    op.drop_index("ix_monitored_locations_group",    table_name="monitored_locations")
    op.drop_table("monitored_locations")
    op.drop_index("ix_alert_subscriptions_active",   table_name="alert_subscriptions")
    op.drop_index("ix_alert_subscriptions_disease",  table_name="alert_subscriptions")
    op.drop_table("alert_subscriptions")
