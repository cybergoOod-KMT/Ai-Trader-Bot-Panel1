"""phase 5 production hardening

Revision ID: 20260630_0006
Revises: 20260630_0005
Create Date: 2026-06-30 15:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0006"
down_revision = "20260630_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("manual_orders", sa.Column("idempotency_key", sa.String(length=120), nullable=True))
    op.create_index("ix_manual_orders_idempotency_key", "manual_orders", ["idempotency_key"], unique=False)
    op.create_index("ix_manual_orders_symbol_mode_created_at", "manual_orders", ["symbol", "mode", "created_at"], unique=False)
    op.create_index("ix_positions_symbol_status_opened_at", "positions", ["symbol", "status", "opened_at"], unique=False)
    op.create_index("ix_trades_symbol_mode_created_at", "trades", ["symbol", "mode", "created_at"], unique=False)
    op.create_index("ix_trades_strategy_created_at", "trades", ["strategy_name", "created_at"], unique=False)
    op.create_index("ix_ai_decisions_symbol_action_created_at", "ai_decisions", ["symbol", "action", "created_at"], unique=False)
    op.add_column("ai_decisions", sa.Column("ai_engine_name", sa.String(length=80), nullable=False, server_default="OPENAI"))
    op.add_column("ai_decisions", sa.Column("strategy_name", sa.String(length=100), nullable=True))
    op.add_column("ai_decisions", sa.Column("learning_memory_json", sa.JSON(), nullable=True))
    op.add_column("bot_configs", sa.Column("ai_engine_name", sa.String(length=80), nullable=False, server_default="OPENAI"))
    op.create_index("ix_bot_decisions_symbol_created_at", "bot_decisions", ["symbol", "created_at"], unique=False)
    op.add_column("bot_decisions", sa.Column("strategy_name", sa.String(length=100), nullable=True))
    op.add_column("bot_decisions", sa.Column("ai_engine_name", sa.String(length=80), nullable=True))

    op.create_table(
        "trade_outcomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("strategy_name", sa.String(length=100), nullable=False),
        sa.Column("ai_engine", sa.String(length=80), nullable=True),
        sa.Column("entry_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("decision_json", sa.JSON(), nullable=False),
        sa.Column("exit_reason", sa.String(length=120), nullable=False),
        sa.Column("pnl", sa.String(length=50), nullable=False),
        sa.Column("pnl_pct", sa.String(length=50), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("was_successful", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trade_outcomes_id"), "trade_outcomes", ["id"], unique=False)
    op.create_index(op.f("ix_trade_outcomes_symbol"), "trade_outcomes", ["symbol"], unique=False)
    op.create_index(op.f("ix_trade_outcomes_strategy_name"), "trade_outcomes", ["strategy_name"], unique=False)
    op.create_index("ix_trade_outcomes_symbol_strategy_created_at", "trade_outcomes", ["symbol", "strategy_name", "created_at"], unique=False)

    op.create_table(
        "learning_memory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("strategy_name", sa.String(length=100), nullable=False),
        sa.Column("stats_json", sa.JSON(), nullable=False),
        sa.Column("lessons_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "strategy_name", name="uq_learning_memory_symbol_strategy"),
    )
    op.create_index(op.f("ix_learning_memory_id"), "learning_memory", ["id"], unique=False)
    op.create_index(op.f("ix_learning_memory_symbol"), "learning_memory", ["symbol"], unique=False)
    op.create_index(op.f("ix_learning_memory_strategy_name"), "learning_memory", ["strategy_name"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index("ix_audit_logs_action_created_at", "audit_logs", ["action", "created_at"], unique=False)
    op.create_index("ix_audit_logs_entity_type_entity_id", "audit_logs", ["entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity_type_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_created_at", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_learning_memory_strategy_name"), table_name="learning_memory")
    op.drop_index(op.f("ix_learning_memory_symbol"), table_name="learning_memory")
    op.drop_index(op.f("ix_learning_memory_id"), table_name="learning_memory")
    op.drop_table("learning_memory")

    op.drop_index("ix_trade_outcomes_symbol_strategy_created_at", table_name="trade_outcomes")
    op.drop_index(op.f("ix_trade_outcomes_strategy_name"), table_name="trade_outcomes")
    op.drop_index(op.f("ix_trade_outcomes_symbol"), table_name="trade_outcomes")
    op.drop_index(op.f("ix_trade_outcomes_id"), table_name="trade_outcomes")
    op.drop_table("trade_outcomes")

    op.drop_column("bot_decisions", "ai_engine_name")
    op.drop_column("bot_decisions", "strategy_name")
    op.drop_index("ix_bot_decisions_symbol_created_at", table_name="bot_decisions")
    op.drop_column("bot_configs", "ai_engine_name")
    op.drop_column("ai_decisions", "learning_memory_json")
    op.drop_column("ai_decisions", "strategy_name")
    op.drop_column("ai_decisions", "ai_engine_name")
    op.drop_index("ix_ai_decisions_symbol_action_created_at", table_name="ai_decisions")
    op.drop_index("ix_trades_strategy_created_at", table_name="trades")
    op.drop_index("ix_trades_symbol_mode_created_at", table_name="trades")
    op.drop_index("ix_positions_symbol_status_opened_at", table_name="positions")
    op.drop_index("ix_manual_orders_symbol_mode_created_at", table_name="manual_orders")
    op.drop_index("ix_manual_orders_idempotency_key", table_name="manual_orders")
    op.drop_column("manual_orders", "idempotency_key")
