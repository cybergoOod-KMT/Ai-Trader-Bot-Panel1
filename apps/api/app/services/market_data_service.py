from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.tabdeal_client import TabdealAPIError, TabdealClient


@dataclass
class MarketDataBundle:
    symbol: str
    rules: dict
    orderbook: dict
    recent_trades: list[dict]
    candles: list[dict]
    source: str
    tabdeal_price: Decimal
    analysis_close: Decimal
    source_price_diff_pct: Decimal


class MarketDataService:
    def __init__(self, tabdeal_client: TabdealClient | None = None) -> None:
        self.settings = get_settings()
        self.tabdeal_client = tabdeal_client or TabdealClient()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        cleaned = symbol.upper().replace("/", "").replace("_", "").replace("-", "").strip()
        if not cleaned.endswith("USDT") and cleaned.isalpha():
            cleaned = f"{cleaned}USDT"
        return cleaned

    async def search_markets(self, query: str) -> list[dict]:
        info = await self.tabdeal_client.get_exchange_info()
        symbols = self.tabdeal_client._extract_symbols(info)
        query_upper = query.upper().replace("_", "").replace("-", "").strip()
        results = []
        for item in symbols:
            symbol = item.get("symbol", "")
            haystack = f"{symbol}{item.get('baseAsset', '')}{item.get('quoteAsset', '')}".upper()
            if not query_upper or query_upper in haystack:
                results.append(
                    {
                        "symbol": symbol,
                        "base_asset": item.get("baseAsset", ""),
                        "quote_asset": item.get("quoteAsset", ""),
                        "status": item.get("status", "UNKNOWN"),
                    }
                )
        return results[:50]

    async def get_market_rules(self, symbol: str) -> dict:
        return await self.tabdeal_client.get_symbol_rules(self.normalize_symbol(symbol))

    async def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        symbol = self.normalize_symbol(symbol)
        raw = await self.tabdeal_client.get_depth(symbol, limit=limit)
        bids = [{"price": row[0], "quantity": row[1]} for row in raw.get("bids", [])]
        asks = [{"price": row[0], "quantity": row[1]} for row in raw.get("asks", [])]
        best_bid = bids[0]["price"] if bids else None
        best_ask = asks[0]["price"] if asks else None
        spread_pct = "0"
        if best_bid and best_ask:
            bid = Decimal(best_bid)
            ask = Decimal(best_ask)
            mid = (bid + ask) / Decimal("2")
            spread_pct = str(((ask - bid) / mid) * Decimal("100"))
        return {
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_pct": spread_pct,
        }

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        symbol = self.normalize_symbol(symbol)
        rows = await self.tabdeal_client.get_recent_trades(symbol, limit=limit)
        normalized = []
        for row in rows:
            normalized.append(
                {
                    "id": row.get("id") or row.get("tradeId"),
                    "price": str(row.get("price")),
                    "quantity": str(row.get("qty") or row.get("quantity")),
                    "timestamp": row.get("time") or row.get("timestamp"),
                    "is_buyer_maker": row.get("isBuyerMaker"),
                }
            )
        return normalized

    async def get_market_snapshot_bundle(self, symbol: str, timeframe: str = "1m", lookback: int = 60) -> MarketDataBundle:
        symbol = self.normalize_symbol(symbol)
        rules = await self.get_market_rules(symbol)
        orderbook = await self.get_orderbook(symbol, limit=20)
        recent_trades = await self.get_recent_trades(symbol, limit=lookback * 5)

        if orderbook["best_bid"] and orderbook["best_ask"]:
            tabdeal_price = (Decimal(orderbook["best_bid"]) + Decimal(orderbook["best_ask"])) / Decimal("2")
        elif recent_trades:
            tabdeal_price = Decimal(recent_trades[0]["price"])
        else:
            raise TabdealAPIError(f"No market data available for {symbol}", code="no_market_data")

        source = "TABDEAL_TRADES_FALLBACK"
        analysis_close = tabdeal_price
        source_price_diff_pct = Decimal("0")

        candles: list[dict]
        try:
            binance_candles = await self._fetch_binance_klines(symbol, timeframe, lookback)
            if binance_candles:
                analysis_close = Decimal(str(binance_candles[-1]["close"]))
                source_price_diff_pct = abs(((analysis_close - tabdeal_price) / tabdeal_price) * Decimal("100"))
                if source_price_diff_pct > Decimal("3"):
                    source = "BINANCE_REJECTED_PRICE_DIFF"
                    candles = self._build_trade_fallback_candles(recent_trades, lookback)
                    analysis_close = Decimal(str(candles[-1]["close"]))
                else:
                    source = "BINANCE_1H_VALIDATED"
                    candles = binance_candles
            else:
                candles = self._build_trade_fallback_candles(recent_trades, lookback)
        except Exception:  # noqa: BLE001
            candles = self._build_trade_fallback_candles(recent_trades, lookback)

        return MarketDataBundle(
            symbol=symbol,
            rules=rules,
            orderbook=orderbook,
            recent_trades=recent_trades,
            candles=candles,
            source=source,
            tabdeal_price=tabdeal_price,
            analysis_close=analysis_close,
            source_price_diff_pct=source_price_diff_pct,
        )

    async def _fetch_binance_klines(self, symbol: str, timeframe: str, lookback: int) -> list[dict]:
        params = {"symbol": symbol, "interval": timeframe, "limit": lookback}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(self.settings.binance_klines_url, params=params)
            if response.status_code >= 400:
                return []
            data = response.json()
        candles = []
        for row in data:
            candles.append(
                {
                    "open_time": int(row[0]),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                    "close_time": int(row[6]),
                }
            )
        return candles

    def _build_trade_fallback_candles(self, trades: list[dict], lookback: int) -> list[dict]:
        now_ms = int(datetime.now(tz=UTC).timestamp() * 1000)
        buckets: dict[int, list[dict]] = defaultdict(list)
        for trade in trades:
            timestamp = int(trade.get("timestamp") or now_ms)
            bucket = timestamp - (timestamp % 60000)
            buckets[bucket].append(trade)

        candles: list[dict] = []
        last_close = float(trades[0]["price"]) if trades else 0.0
        for index in range(lookback - 1, -1, -1):
            bucket_time = now_ms - (index * 60000)
            bucket_time -= bucket_time % 60000
            bucket_trades = buckets.get(bucket_time, [])
            if bucket_trades:
                prices = [float(item["price"]) for item in bucket_trades]
                quantities = [float(item["quantity"]) for item in bucket_trades]
                open_price = prices[-1]
                close_price = prices[0]
                high_price = max(prices)
                low_price = min(prices)
                volume = sum(quantities)
                last_close = close_price
            else:
                open_price = high_price = low_price = close_price = last_close
                volume = 0.0
            candles.append(
                {
                    "open_time": bucket_time,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                    "close_time": bucket_time + 59999,
                }
            )
        return candles
