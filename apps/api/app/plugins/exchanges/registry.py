from __future__ import annotations

from fastapi import HTTPException, status

from app.plugins.exchanges.binance_public_data import BinancePublicDataConnector
from app.plugins.exchanges.tabdeal_connector import TabdealConnector


class ExchangeRegistry:
    def list_connectors(self) -> list[dict]:
        return [
            {"name": "TABDEAL", "capabilities": TabdealConnector.capabilities},
            {"name": "BINANCE_PUBLIC", "capabilities": BinancePublicDataConnector.capabilities},
        ]

    def get(self, name: str, **kwargs):
        connector_name = name.upper()
        if connector_name == "TABDEAL":
            return TabdealConnector(kwargs.get("api_key"), kwargs.get("api_secret"))
        if connector_name == "BINANCE_PUBLIC":
            return BinancePublicDataConnector()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange connector not found.")


exchange_registry = ExchangeRegistry()
