"""phase 3 ai bots

Revision ID: 20260630_0004
Revises: 20260630_0003
Create Date: 2026-06-30 02:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0004"
down_revision = "20260630_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_account_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("entry_note", sa.Text(), nullable=False),
        sa.Column("entry_price", sa.String(length=50), nullable=True),
        sa.Column("breakout_price", sa.String(length=50), nullable=True),
        sa.Column("pullback_price", sa.String(length=50), nullable=True),
        sa.Column("take_profit_pct", sa.String(length=50), nullable=False),
        sa.Column("stop_loss_pct", sa.String(length=50), nullable=False),
        sa.Column("risk_warning", sa.Text(), nullable=False),
        sa.Column("technical_summary_json", sa.JSON(), nullable=False),
        sa.Column("market_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("account_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("guard_result_json", sa.JSON(), nullable=True),
        sa.Column("risk_result_json", sa.JSON(), nullable=True),
        sa.Column("executed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("execution_order_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_decisions_id"), "ai_decisions", ["id"], unique=False)
    op.create_index(op.f("ix_ai_decisions_api_account_id"), "ai_decisions", ["api_account_id"], unique=False)
    op.create_index(op.f("ix_ai_decisions_symbol"), "ai_decisions", ["symbol"], unique=False)
    op.create_index(op.f("ix_ai_decisions_action"), "ai_decisions", ["action"], unique=False)
    op.create_index(op.f("ix_ai_decisions_execution_order_id"), "ai_decisions", ["execution_order_id"], unique=False)

    op.create_table(
        "bot_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("api_account_id", sa.Integer(), nullable=False),
        sa.Column("symbols_json", sa.JSON(), nullable=False),
        sa.Column("max_total_budget_usdt", sa.String(length=50), nullable=False),
        sa.Column("per_order_usdt", sa.String(length=50), nullable=False),
        sa.Column("max_open_positions", sa.Integer(), nullable=False),
        sa.Column("max_daily_loss_pct", sa.String(length=50), nullable=False),
        sa.Column("min_ai_confidence", sa.Integer(), nullable=False),
        sa.Column("technical_guard_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("strategy_name", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("api_error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("real_start_confirm_token_hash", sa.String(length=255), nullable=True),
        sa.Column("real_start_confirm_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("real_start_confirm_token_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_bot_configs_id"), "bot_configs", ["id"], unique=False)
    op.create_index(op.f("ix_bot_configs_name"), "bot_configs", ["name"], unique=False)
    op.create_index(op.f("ix_bot_configs_api_account_id"), "bot_configs", ["api_account_id"], unique=False)

    op.create_table(
        "bot_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bot_config_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_runs_id"), "bot_runs", ["id"], unique=False)
    op.create_index(op.f("ix_bot_runs_bot_config_id"), "bot_runs", ["bot_config_id"], unique=False)
    op.create_index(op.f("ix_bot_runs_status"), "bot_runs", ["status"], unique=False)

    op.create_table(
        "bot_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bot_run_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("market_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("ai_decision_id", sa.Integer(), nullable=True),
        sa.Column("guard_result_json", sa.JSON(), nullable=True),
        sa.Column("risk_result_json", sa.JSON(), nullable=True),
        sa.Column("executed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_decisions_id"), "bot_decisions", ["id"], unique=False)
    op.create_index(op.f("ix_bot_decisions_bot_run_id"), "bot_decisions", ["bot_run_id"], unique=False)
    op.create_index(op.f("ix_bot_decisions_symbol"), "bot_decisions", ["symbol"], unique=False)
    op.create_index(op.f("ix_bot_decisions_ai_decision_id"), "bot_decisions", ["ai_decision_id"], unique=False)

    op.create_table(
        "watch_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bot_run_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("trigger_price", sa.String(length=50), nullable=False),
        sa.Column("invalidation_price", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_watch_tasks_id"), "watch_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_watch_tasks_bot_run_id"), "watch_tasks", ["bot_run_id"], unique=False)
    op.create_index(op.f("ix_watch_tasks_symbol"), "watch_tasks", ["symbol"], unique=False)
    op.create_index(op.f("ix_watch_tasks_status"), "watch_tasks", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_watch_tasks_status"), table_name="watch_tasks")
    op.drop_index(op.f("ix_watch_tasks_symbol"), table_name="watch_tasks")
    op.drop_index(op.f("ix_watch_tasks_bot_run_id"), table_name="watch_tasks")
    op.drop_index(op.f("ix_watch_tasks_id"), table_name="watch_tasks")
    op.drop_table("watch_tasks")

    op.drop_index(op.f("ix_bot_decisions_ai_decision_id"), table_name="bot_decisions")
    op.drop_index(op.f("ix_bot_decisions_symbol"), table_name="bot_decisions")
    op.drop_index(op.f("ix_bot_decisions_bot_run_id"), table_name="bot_decisions")
    op.drop_index(op.f("ix_bot_decisions_id"), table_name="bot_decisions")
    op.drop_table("bot_decisions")

    op.drop_index(op.f("ix_bot_runs_status"), table_name="bot_runs")
    op.drop_index(op.f("ix_bot_runs_bot_config_id"), table_name="bot_runs")
    op.drop_index(op.f("ix_bot_runs_id"), table_name="bot_runs")
    op.drop_table("bot_runs")

    op.drop_index(op.f("ix_bot_configs_api_account_id"), table_name="bot_configs")
    op.drop_index(op.f("ix_bot_configs_name"), table_name="bot_configs")
    op.drop_index(op.f("ix_bot_configs_id"), table_name="bot_configs")
    op.drop_table("bot_configs")

    op.drop_index(op.f("ix_ai_decisions_execution_order_id"), table_name="ai_decisions")
    op.drop_index(op.f("ix_ai_decisions_action"), table_name="ai_decisions")
    op.drop_index(op.f("ix_ai_decisions_symbol"), table_name="ai_decisions")
    op.drop_index(op.f("ix_ai_decisions_api_account_id"), table_name="ai_decisions")
    op.drop_index(op.f("ix_ai_decisions_id"), table_name="ai_decisions")
    op.drop_table("ai_decisions")
