"""add webhook_url to alert_subscriptions and prediction_feedback table

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-06 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alert_subscriptions",
        sa.Column("webhook_url", sa.String(512), nullable=True),
    )

    op.create_table(
        "prediction_feedback",
        sa.Column("id",             sa.Integer(),  primary_key=True),
        sa.Column("prediction_id",  sa.Integer(),  nullable=False),
        sa.Column("observed_cases", sa.Integer(),  nullable=False),
        sa.Column("notes",          sa.Text(),     nullable=True),
        sa.Column("submitted_at",   sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_prediction_feedback_prediction_id",
        "prediction_feedback",
        ["prediction_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_prediction_feedback_prediction_id", table_name="prediction_feedback")
    op.drop_table("prediction_feedback")
    op.drop_column("alert_subscriptions", "webhook_url")
