from __future__ import annotations

from app.core.config import get_settings
from app.plugins.exchanges.base import BaseExchangeConnector


class BinancePublicDataConnector(BaseExchangeConnector):
    name = "BINANCE_PUBLIC"
    capabilities = ["market_data"]

    async def healthcheck(self) -> dict:
        settings = get_settings()
        return {"ok": True, "klines_url": settings.binance_klines_url}
