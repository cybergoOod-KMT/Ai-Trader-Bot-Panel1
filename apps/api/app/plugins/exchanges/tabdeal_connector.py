from __future__ import annotations

from app.plugins.exchanges.base import BaseExchangeConnector
from app.services.tabdeal_client import TabdealClient


class TabdealConnector(BaseExchangeConnector):
    name = "TABDEAL"
    capabilities = ["account", "orders", "market_data", "trading"]

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.client = TabdealClient(api_key, api_secret)

    async def healthcheck(self) -> dict:
        return await self.client.ping()
