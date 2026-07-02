from datetime import datetime

from pydantic import BaseModel


class BotConfigRequest(BaseModel):
    name: str
    mode: str
    api_account_id: int
    symbols_json: list[str]
    max_total_budget_usdt: str
    per_order_usdt: str
    max_open_positions: int
    max_daily_loss_pct: str
    min_ai_confidence: int = 60
    technical_guard_enabled: bool = True
    strategy_name: str
    ai_engine_name: str = "OPENAI"


class BotStartStopRequest(BaseModel):
    confirm_token: str | None = None


class BotConfigResponse(BaseModel):
    id: int
    name: str
    mode: str
    api_account_id: int
    symbols_json: list[str]
    max_total_budget_usdt: str
    per_order_usdt: str
    max_open_positions: int
    max_daily_loss_pct: str
    min_ai_confidence: int
    technical_guard_enabled: bool
    strategy_name: str
    ai_engine_name: str
    is_active: bool
    api_error_count: int
    created_at: datetime
    updated_at: datetime


class BotRunResponse(BaseModel):
    id: int
    bot_config_id: int
    status: str
    started_at: datetime
    stopped_at: datetime | None
    error_message: str | None


class BotDecisionResponse(BaseModel):
    id: int
    bot_run_id: int
    symbol: str
    action: str
    confidence: int
    reason: str
    market_snapshot_json: dict
    ai_decision_id: int | None
    guard_result_json: dict | None
    risk_result_json: dict | None
    strategy_name: str | None = None
    ai_engine_name: str | None = None
    executed: bool
    created_at: datetime


class BotStartResponse(BaseModel):
    status: str
    bot_run_id: int | None = None
    confirm_token: str | None = None
