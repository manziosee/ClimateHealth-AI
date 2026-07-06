"""add api_keys table

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-05 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id",             sa.Integer(),    primary_key=True),
        sa.Column("name",           sa.String(100),  nullable=False),
        sa.Column("key_prefix",     sa.String(12),   nullable=False),
        sa.Column("key_hash",       sa.String(64),   nullable=False, unique=True),
        sa.Column("is_active",      sa.Boolean(),    server_default=sa.true()),
        sa.Column("requests_total", sa.Integer(),    server_default="0"),
        sa.Column("last_used_at",   sa.DateTime(),   nullable=True),
        sa.Column("created_at",     sa.DateTime(),   server_default=sa.func.now()),
    )
    op.create_index("ix_api_keys_key_hash",  "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_is_active", "api_keys", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_is_active", table_name="api_keys")
    op.drop_index("ix_api_keys_key_hash",  table_name="api_keys")
    op.drop_table("api_keys")
