from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    source: str
    message: str
    created_at: datetime


class DashboardNotificationCount(BaseModel):
    unread: int


class ActiveApiAccountSummary(BaseModel):
    id: int
    name: str
    read_only: bool
    real_trading_allowed: bool
    has_tabdeal_credentials: bool
    has_openai_api_key: bool


class DashboardResponse(BaseModel):
    api_status: str
    openai_status: str
    active_api_account: ActiveApiAccountSummary | None
    latest_system_logs: list[DashboardLogItem]
    balances: list[dict]
    open_orders: list[dict]
    open_positions: list[dict]
    latest_trades: list[dict]
    active_bots: list[dict]
    active_watches: list[dict]
    latest_ai_decisions: list[dict]
    latest_strategy_decisions: list[dict]
    active_script_runs: list[dict]
    latest_notifications: list[dict]
    pnl_chart: list[dict]
    today_dry_run_pnl: str
    today_real_pnl: str
    bot_health: dict
    unread_notifications_count: int
    real_trading_enabled: bool
    dry_run_default: bool
    phase: str
