"""position close confirm tokens

Revision ID: 20260630_0003
Revises: 20260630_0002
Create Date: 2026-06-30 01:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0003"
down_revision = "20260630_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("positions", sa.Column("close_confirm_token_hash", sa.String(length=255), nullable=True))
    op.add_column("positions", sa.Column("close_confirm_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("positions", sa.Column("close_confirm_token_used_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("positions", "close_confirm_token_used_at")
    op.drop_column("positions", "close_confirm_token_expires_at")
    op.drop_column("positions", "close_confirm_token_hash")
