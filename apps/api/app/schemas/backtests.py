from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BacktestRunRequest(BaseModel):
    strategy_name: str
    symbol: str
    timeframe: str = "1m"
    start_time: datetime
    end_time: datetime
    initial_balance: float = Field(gt=0)
    config_json: dict = Field(default_factory=dict)
    csv_dataset_id: str | None = None


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_name: str
    symbol: str
    timeframe: str
    start_time: datetime
    end_time: datetime
    initial_balance: str
    final_balance: str
    net_pnl: str
    net_pnl_pct: str
    max_drawdown: str
    win_rate: str
    profit_factor: str
    config_json: dict
    result_json: dict
    created_at: datetime


class BacktestTradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backtest_run_id: int
    symbol: str
    side: str
    entry_price: str
    exit_price: str
    quantity: str
    pnl: str
    pnl_pct: str
    opened_at: datetime
    closed_at: datetime
    reason: str


class BacktestEquityPoint(BaseModel):
    timestamp: datetime
    equity: float
    drawdown_pct: float
