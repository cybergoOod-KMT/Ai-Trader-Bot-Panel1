from datetime import datetime

from pydantic import BaseModel


class WatchTaskResponse(BaseModel):
    id: int
    bot_run_id: int
    symbol: str
    type: str
    trigger_price: str
    invalidation_price: str | None
    status: str
    reason: str
    created_at: datetime
    updated_at: datetime
