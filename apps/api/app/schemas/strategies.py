from pydantic import BaseModel


class StrategyAnalyzeRequest(BaseModel):
    symbol: str
    config: dict = {}


class StrategyDecisionResponse(BaseModel):
    action: str
    confidence: int
    reason: str
    entry_price: float | None
    take_profit_pct: float | None
    stop_loss_pct: float | None
    metadata: dict
