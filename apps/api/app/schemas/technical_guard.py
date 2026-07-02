from pydantic import BaseModel


class TechnicalGuardCheckRequest(BaseModel):
    symbol: str


class TechnicalGuardResponse(BaseModel):
    allowed: bool
    reasons: list[str]
    risk_reward: str
    entry_type: str
