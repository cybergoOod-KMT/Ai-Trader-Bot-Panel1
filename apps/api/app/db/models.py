from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ApiAccount(TimestampMixin, Base):
    __tablename__ = "api_accounts"
    __table_args__ = (UniqueConstraint("name", name="uq_api_accounts_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    tabdeal_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    tabdeal_api_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    openai_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    openai_model: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    real_trading_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SystemSetting(TimestampMixin, Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    value_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ManualOrder(Base):
    __tablename__ = "manual_orders"
    __table_args__ = (
        Index("ix_manual_orders_symbol_mode_created_at", "symbol", "mode", "created_at"),
        Index("ix_manual_orders_idempotency_key", "idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    api_account_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estimated_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirm_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirm_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirm_token_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_symbol_status_opened_at", "symbol", "status", "opened_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    base_asset: Mapped[str] = mapped_column(String(20), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_price: Mapped[str] = mapped_column(String(50), nullable=False)
    current_price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    take_profit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stop_loss: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    opened_by: Mapped[str] = mapped_column(String(50), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pnl: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pnl_pct: Mapped[str | None] = mapped_column(String(50), nullable=True)
    close_confirm_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    close_confirm_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_confirm_token_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_symbol_mode_created_at", "symbol", "mode", "created_at"),
        Index("ix_trades_strategy_created_at", "strategy_name", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(50), nullable=False)
    fee: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    strategy_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pnl: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AiDecision(Base):
    __tablename__ = "ai_decisions"
    __table_args__ = (
        Index("ix_ai_decisions_symbol_action_created_at", "symbol", "action", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    api_account_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    entry_note: Mapped[str] = mapped_column(Text, nullable=False)
    entry_price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    breakout_price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pullback_price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    take_profit_pct: Mapped[str] = mapped_column(String(50), nullable=False)
    stop_loss_pct: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_warning: Mapped[str] = mapped_column(Text, nullable=False)
    technical_summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    market_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    account_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    guard_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_engine_name: Mapped[str] = mapped_column(String(80), nullable=False, default="OPENAI")
    strategy_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    learning_memory_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    execution_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BotConfig(TimestampMixin, Base):
    __tablename__ = "bot_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    api_account_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbols_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    max_total_budget_usdt: Mapped[str] = mapped_column(String(50), nullable=False)
    per_order_usdt: Mapped[str] = mapped_column(String(50), nullable=False)
    max_open_positions: Mapped[int] = mapped_column(Integer, nullable=False)
    max_daily_loss_pct: Mapped[str] = mapped_column(String(50), nullable=False)
    min_ai_confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    technical_guard_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    ai_engine_name: Mapped[str] = mapped_column(String(80), nullable=False, default="OPENAI")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    api_error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    real_start_confirm_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    real_start_confirm_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    real_start_confirm_token_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BotRun(Base):
    __tablename__ = "bot_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_config_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class BotDecision(Base):
    __tablename__ = "bot_decisions"
    __table_args__ = (
        Index("ix_bot_decisions_symbol_created_at", "symbol", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    market_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ai_decision_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    guard_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    strategy_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_engine_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WatchTask(TimestampMixin, Base):
    __tablename__ = "watch_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    trigger_price: Mapped[str] = mapped_column(String(50), nullable=False)
    invalidation_price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class ScriptFile(TimestampMixin, Base):
    __tablename__ = "script_files"
    __table_args__ = (UniqueConstraint("relative_path", name="uq_script_files_relative_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(400), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScriptRun(Base):
    __tablename__ = "script_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    script_file_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScriptLog(Base):
    __tablename__ = "script_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    script_run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    stream: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    line: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    initial_balance: Mapped[str] = mapped_column(String(50), nullable=False)
    final_balance: Mapped[str] = mapped_column(String(50), nullable=False)
    net_pnl: Mapped[str] = mapped_column(String(50), nullable=False)
    net_pnl_pct: Mapped[str] = mapped_column(String(50), nullable=False)
    max_drawdown: Mapped[str] = mapped_column(String(50), nullable=False)
    win_rate: Mapped[str] = mapped_column(String(50), nullable=False)
    profit_factor: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backtest_run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_price: Mapped[str] = mapped_column(String(50), nullable=False)
    exit_price: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    pnl: Mapped[str] = mapped_column(String(50), nullable=False)
    pnl_pct: Mapped[str] = mapped_column(String(50), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class TradeOutcome(Base):
    __tablename__ = "trade_outcomes"
    __table_args__ = (
        Index("ix_trade_outcomes_symbol_strategy_created_at", "symbol", "strategy_name", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ai_engine: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entry_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    decision_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    exit_reason: Mapped[str] = mapped_column(String(120), nullable=False)
    pnl: Mapped[str] = mapped_column(String(50), nullable=False)
    pnl_pct: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    was_successful: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LearningMemory(Base):
    __tablename__ = "learning_memory"
    __table_args__ = (UniqueConstraint("symbol", "strategy_name", name="uq_learning_memory_symbol_strategy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    stats_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    lessons_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_action_created_at", "action", "created_at"),
        Index("ix_audit_logs_entity_type_entity_id", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
