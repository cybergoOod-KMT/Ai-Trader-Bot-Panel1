from datetime import datetime

from pydantic import BaseModel


class ReportSummaryResponse(BaseModel):
    trades_count: int
    ai_decisions_count: int
    bot_decisions_count: int
    backtests_count: int
    script_runs_count: int
    dry_run_pnl: float
    real_pnl: float


class ReportFilterParams(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    symbol: str | None = None
    strategy: str | None = None
    mode: str | None = None


class PnlBucket(BaseModel):
    key: str
    pnl: float
    count: int
