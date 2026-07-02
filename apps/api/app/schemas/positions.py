from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    base_asset: str
    quote_asset: str
    quantity: str
    entry_price: str
    current_price: str | None
    take_profit: str | None
    stop_loss: str | None
    status: str
    source: str
    opened_by: str
    opened_at: datetime
    closed_at: datetime | None
    pnl: str | None
    pnl_pct: str | None


class PositionClosePreviewResponse(BaseModel):
    position_id: int
    symbol: str
    quantity: str
    estimated_close_price: str
    estimated_value: str
    mode: str
    reasons: list[str]
    confirm_token: str | None = None


class PositionCloseRequest(BaseModel):
    confirm_token: str | None = None


class PositionTpSlRequest(BaseModel):
    take_profit: str | None = None
    stop_loss: str | None = None
