"""phase 4 operations

Revision ID: 20260630_0005
Revises: 20260630_0004
Create Date: 2026-06-30 11:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0005"
down_revision = "20260630_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("severity", sa.String(length=20), nullable=False, server_default="INFO"))

    op.create_table(
        "script_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("relative_path", sa.String(length=400), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("relative_path", name="uq_script_files_relative_path"),
    )
    op.create_index(op.f("ix_script_files_id"), "script_files", ["id"], unique=False)
    op.create_index(op.f("ix_script_files_relative_path"), "script_files", ["relative_path"], unique=False)

    op.create_table(
        "script_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("script_file_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_runs_id"), "script_runs", ["id"], unique=False)
    op.create_index(op.f("ix_script_runs_script_file_id"), "script_runs", ["script_file_id"], unique=False)
    op.create_index(op.f("ix_script_runs_status"), "script_runs", ["status"], unique=False)

    op.create_table(
        "script_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("script_run_id", sa.Integer(), nullable=False),
        sa.Column("stream", sa.String(length=20), nullable=False),
        sa.Column("line", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_logs_id"), "script_logs", ["id"], unique=False)
    op.create_index(op.f("ix_script_logs_script_run_id"), "script_logs", ["script_run_id"], unique=False)
    op.create_index(op.f("ix_script_logs_stream"), "script_logs", ["stream"], unique=False)

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_name", sa.String(length=80), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("timeframe", sa.String(length=20), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("initial_balance", sa.String(length=50), nullable=False),
        sa.Column("final_balance", sa.String(length=50), nullable=False),
        sa.Column("net_pnl", sa.String(length=50), nullable=False),
        sa.Column("net_pnl_pct", sa.String(length=50), nullable=False),
        sa.Column("max_drawdown", sa.String(length=50), nullable=False),
        sa.Column("win_rate", sa.String(length=50), nullable=False),
        sa.Column("profit_factor", sa.String(length=50), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtest_runs_id"), "backtest_runs", ["id"], unique=False)
    op.create_index(op.f("ix_backtest_runs_strategy_name"), "backtest_runs", ["strategy_name"], unique=False)
    op.create_index(op.f("ix_backtest_runs_symbol"), "backtest_runs", ["symbol"], unique=False)

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=40), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("entry_price", sa.String(length=50), nullable=False),
        sa.Column("exit_price", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.String(length=50), nullable=False),
        sa.Column("pnl", sa.String(length=50), nullable=False),
        sa.Column("pnl_pct", sa.String(length=50), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtest_trades_id"), "backtest_trades", ["id"], unique=False)
    op.create_index(op.f("ix_backtest_trades_backtest_run_id"), "backtest_trades", ["backtest_run_id"], unique=False)
    op.create_index(op.f("ix_backtest_trades_symbol"), "backtest_trades", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_backtest_trades_symbol"), table_name="backtest_trades")
    op.drop_index(op.f("ix_backtest_trades_backtest_run_id"), table_name="backtest_trades")
    op.drop_index(op.f("ix_backtest_trades_id"), table_name="backtest_trades")
    op.drop_table("backtest_trades")

    op.drop_index(op.f("ix_backtest_runs_symbol"), table_name="backtest_runs")
    op.drop_index(op.f("ix_backtest_runs_strategy_name"), table_name="backtest_runs")
    op.drop_index(op.f("ix_backtest_runs_id"), table_name="backtest_runs")
    op.drop_table("backtest_runs")

    op.drop_index(op.f("ix_script_logs_stream"), table_name="script_logs")
    op.drop_index(op.f("ix_script_logs_script_run_id"), table_name="script_logs")
    op.drop_index(op.f("ix_script_logs_id"), table_name="script_logs")
    op.drop_table("script_logs")

    op.drop_index(op.f("ix_script_runs_status"), table_name="script_runs")
    op.drop_index(op.f("ix_script_runs_script_file_id"), table_name="script_runs")
    op.drop_index(op.f("ix_script_runs_id"), table_name="script_runs")
    op.drop_table("script_runs")

    op.drop_index(op.f("ix_script_files_relative_path"), table_name="script_files")
    op.drop_index(op.f("ix_script_files_id"), table_name="script_files")
    op.drop_table("script_files")

    op.drop_column("notifications", "severity")
