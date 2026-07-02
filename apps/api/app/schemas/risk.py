from pydantic import BaseModel


class RiskCheckRequest(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: str | None = None
    price: str | None = None
    usdt_amount: str | None = None
    prefer_real_execution: bool = False


class RiskCheckResponse(BaseModel):
    allowed: bool
    reasons: list[str]
    calculated_quantity: str
    estimated_value: str
    mode: str
