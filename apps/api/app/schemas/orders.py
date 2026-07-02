from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.risk import RiskCheckResponse
from app.schemas.technical_guard import TechnicalGuardResponse


class ManualOrderRequest(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: str | None = None
    price: str | None = None
    usdt_amount: str | None = None
    prefer_real_execution: bool = False


class ConfirmRealOrderRequest(BaseModel):
    confirm_token: str


class ManualOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    api_account_id: int
    symbol: str
    side: str
    order_type: str
    quantity: str
    price: str | None
    estimated_value: str | None
    mode: str
    status: str
    exchange_order_id: str | None
    response_json: dict | None
    error_message: str | None
    created_at: datetime


class ManualOrderPreviewResponse(BaseModel):
    symbol: str
    normalized_quantity: str
    normalized_price: str | None
    estimated_value: str
    market_snapshot: dict
    risk: RiskCheckResponse
    technical_guard: TechnicalGuardResponse | None


class ManualOrderCreateResponse(BaseModel):
    order: ManualOrderResponse
    preview: ManualOrderPreviewResponse
    confirm_token: str | None = None
