from datetime import datetime

from pydantic import BaseModel


class AiAnalyzeRequest(BaseModel):
    symbol: str


class AiExecuteRequest(BaseModel):
    decision_id: int
    prefer_real_execution: bool = False
    confirm_token: str | None = None


class AiDecisionResponse(BaseModel):
    id: int
    api_account_id: int
    symbol: str
    action: str
    confidence: int
    reason: str
    entry_note: str
    entry_price: str | None
    breakout_price: str | None
    pullback_price: str | None
    take_profit_pct: str
    stop_loss_pct: str
    risk_warning: str
    technical_summary_json: dict
    market_snapshot_json: dict
    account_snapshot_json: dict
    guard_result_json: dict | None
    risk_result_json: dict | None
    ai_engine_name: str
    strategy_name: str | None
    learning_memory_json: dict | None
    executed: bool
    execution_order_id: int | None
    created_at: datetime


class AiExecuteResponse(BaseModel):
    decision: AiDecisionResponse
    order: dict
    preview: dict | None = None
    confirm_token: str | None = None
