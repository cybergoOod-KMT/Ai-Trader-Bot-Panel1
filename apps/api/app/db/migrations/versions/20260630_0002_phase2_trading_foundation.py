"""phase 2 trading foundation"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0002"
down_revision = "20260629_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manual_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("api_account_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.String(length=50), nullable=False),
        sa.Column("price", sa.String(length=50), nullable=True),
        sa.Column("estimated_value", sa.String(length=50), nullable=True),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("exchange_order_id", sa.String(length=80), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("confirm_token_hash", sa.String(length=255), nullable=True),
        sa.Column("confirm_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirm_token_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_manual_orders_id", "manual_orders", ["id"])
    op.create_index("ix_manual_orders_api_account_id", "manual_orders", ["api_account_id"])
    op.create_index("ix_manual_orders_symbol", "manual_orders", ["symbol"])
    op.create_index("ix_manual_orders_mode", "manual_orders", ["mode"])
    op.create_index("ix_manual_orders_status", "manual_orders", ["status"])
    op.create_index("ix_manual_orders_exchange_order_id", "manual_orders", ["exchange_order_id"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("base_asset", sa.String(length=20), nullable=False),
        sa.Column("quote_asset", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.String(length=50), nullable=False),
        sa.Column("entry_price", sa.String(length=50), nullable=False),
        sa.Column("current_price", sa.String(length=50), nullable=True),
        sa.Column("take_profit", sa.String(length=50), nullable=True),
        sa.Column("stop_loss", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("opened_by", sa.String(length=50), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pnl", sa.String(length=50), nullable=True),
        sa.Column("pnl_pct", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_positions_id", "positions", ["id"])
    op.create_index("ix_positions_symbol", "positions", ["symbol"])
    op.create_index("ix_positions_status", "positions", ["status"])

    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.String(length=50), nullable=False),
        sa.Column("price", sa.String(length=50), nullable=False),
        sa.Column("value", sa.String(length=50), nullable=False),
        sa.Column("fee", sa.String(length=50), nullable=True),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("strategy_name", sa.String(length=100), nullable=True),
        sa.Column("pnl", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trades_id", "trades", ["id"])
    op.create_index("ix_trades_symbol", "trades", ["symbol"])
    op.create_index("ix_trades_mode", "trades", ["mode"])


def downgrade() -> None:
    op.drop_index("ix_trades_mode", table_name="trades")
    op.drop_index("ix_trades_symbol", table_name="trades")
    op.drop_index("ix_trades_id", table_name="trades")
    op.drop_table("trades")

    op.drop_index("ix_positions_status", table_name="positions")
    op.drop_index("ix_positions_symbol", table_name="positions")
    op.drop_index("ix_positions_id", table_name="positions")
    op.drop_table("positions")

    op.drop_index("ix_manual_orders_exchange_order_id", table_name="manual_orders")
    op.drop_index("ix_manual_orders_status", table_name="manual_orders")
    op.drop_index("ix_manual_orders_mode", table_name="manual_orders")
    op.drop_index("ix_manual_orders_symbol", table_name="manual_orders")
    op.drop_index("ix_manual_orders_api_account_id", table_name="manual_orders")
    op.drop_index("ix_manual_orders_id", table_name="manual_orders")
    op.drop_table("manual_orders")
