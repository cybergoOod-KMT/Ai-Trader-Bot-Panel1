import asyncio
import hashlib
import hmac
import random
import time
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


class TabdealAPIError(Exception):
    def __init__(self, message: str, code: str | int | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class TabdealClient:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8") if api_secret else None
        self.base_url = get_settings().tabdeal_base_url.rstrip("/")
        self.public_prefix = "/r/api/v1"
        self.private_prefix = "/r/api/v1"
        self.order_prefix = "/api/v1"

    async def ping(self) -> dict:
        return await self._request("GET", f"{self.public_prefix}/ping")

    async def get_exchange_info(self, symbol: str | None = None, symbols: list[str] | None = None) -> dict:
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        if symbols:
            params["symbols"] = ",".join(symbols)
        return await self._request("GET", f"{self.public_prefix}/exchangeInfo", params=params)

    async def get_symbol_rules(self, symbol: str) -> dict:
        info = await self.get_exchange_info(symbol=symbol)
        symbols = self._extract_symbols(info)
        if not symbols:
            raise TabdealAPIError(f"Invalid symbol: {symbol}", code="invalid_symbol")
        item = symbols[0]
        filters = item.get("filters") or []
        parsed = {
            "symbol": item.get("symbol", symbol),
            "base_asset": item.get("baseAsset") or symbol[:-4],
            "quote_asset": item.get("quoteAsset") or symbol[-4:],
            "status": item.get("status", "UNKNOWN"),
            "price_precision": int(item.get("pricePrecision", 8) or 8),
            "quantity_precision": int(item.get("quantityPrecision", 8) or 8),
            "filters": filters,
            "tick_size": None,
            "step_size": None,
            "min_qty": None,
            "min_notional": None,
        }
        for filter_item in filters:
            filter_type = filter_item.get("filterType")
            if filter_type == "PRICE_FILTER":
                parsed["tick_size"] = str(filter_item.get("tickSize"))
            elif filter_type == "LOT_SIZE":
                parsed["step_size"] = str(filter_item.get("stepSize"))
                parsed["min_qty"] = str(filter_item.get("minQty"))
            elif filter_type in {"MIN_NOTIONAL", "NOTIONAL"}:
                parsed["min_notional"] = str(filter_item.get("minNotional") or filter_item.get("notional"))
        return parsed

    async def get_depth(self, symbol: str, limit: int = 20) -> dict:
        return await self._request("GET", f"{self.public_prefix}/depth", params={"symbol": symbol, "limit": limit})

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        return await self._request("GET", f"{self.public_prefix}/trades", params={"symbol": symbol, "limit": limit})

    async def get_account(self) -> dict:
        return await self._signed_request("GET", f"{self.private_prefix}/account")

    async def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        params = {"symbol": symbol} if symbol else None
        return await self._signed_request("GET", f"{self.private_prefix}/openOrders", params=params)

    async def get_all_orders(self, symbol: str, limit: int = 50) -> list[dict]:
        return await self._signed_request("GET", f"{self.private_prefix}/allOrders", params={"symbol": symbol, "limit": limit})

    async def get_my_trades(self, symbol: str, limit: int = 50) -> list[dict]:
        return await self._signed_request("GET", f"{self.private_prefix}/myTrades", params={"symbol": symbol, "limit": limit})

    async def create_market_order(self, symbol: str, side: str, quantity: str) -> dict:
        return await self._signed_request(
            "POST",
            f"{self.order_prefix}/order",
            params={"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity},
        )

    async def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> dict:
        return await self._signed_request(
            "POST",
            f"{self.order_prefix}/order",
            params={
                "symbol": symbol,
                "side": side,
                "type": "LIMIT",
                "quantity": quantity,
                "price": price,
            },
        )

    async def cancel_order(self, symbol: str, order_id: str | int) -> dict:
        return await self._signed_request(
            "DELETE",
            f"{self.order_prefix}/order",
            params={"symbol": symbol, "orderId": str(order_id)},
        )

    def normalize_quantity(self, rules: dict, raw_qty: str | float | Decimal) -> str:
        qty = self._to_decimal(raw_qty, "invalid quantity")
        if qty <= 0:
            raise TabdealAPIError("invalid quantity", code="invalid_quantity")
        step_size = self._to_decimal(rules.get("step_size") or "0.00000001")
        normalized = self._quantize_to_step(qty, step_size)
        return self._decimal_to_str(normalized)

    def normalize_price(self, rules: dict, raw_price: str | float | Decimal) -> str:
        price = self._to_decimal(raw_price, "invalid price")
        if price <= 0:
            raise TabdealAPIError("invalid price", code="invalid_price")
        tick_size = self._to_decimal(rules.get("tick_size") or "0.00000001")
        normalized = self._quantize_to_step(price, tick_size)
        return self._decimal_to_str(normalized)

    def validate_order(
        self,
        rules: dict,
        side: str,
        quantity: str,
        price: str | None = None,
    ) -> dict:
        normalized_qty = self.normalize_quantity(rules, quantity)
        normalized_price = self.normalize_price(rules, price) if price is not None else None
        qty_dec = self._to_decimal(normalized_qty)
        price_for_value = self._to_decimal(normalized_price or price or "0")
        min_qty = rules.get("min_qty")
        if min_qty and qty_dec < self._to_decimal(min_qty):
            raise TabdealAPIError("invalid quantity below minQty", code="invalid_quantity")
        if normalized_price:
            min_notional = rules.get("min_notional")
            if min_notional and qty_dec * price_for_value < self._to_decimal(min_notional):
                raise TabdealAPIError("order value is below minNotional", code="min_notional")
        return {
            "symbol": rules["symbol"],
            "side": side.upper(),
            "quantity": normalized_qty,
            "price": normalized_price,
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        attempt = 0
        last_exc: Exception | None = None
        while attempt < 3:
            try:
                headers = {"X-MBX-APIKEY": self.api_key} if signed and self.api_key else {}
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.request(method, f"{self.base_url}{path}", params=params, headers=headers)
                if response.status_code == 502:
                    raise TabdealAPIError("upstream 502 from Tabdeal", code="bad_gateway", status_code=502)
                response.raise_for_status()
                return response.json() if response.content else {}
            except httpx.TimeoutException as exc:
                last_exc = TabdealAPIError("timeout while talking to Tabdeal", code="timeout")
            except httpx.NetworkError as exc:
                last_exc = TabdealAPIError("network unavailable while talking to Tabdeal", code="network_unavailable")
            except httpx.HTTPStatusError as exc:
                last_exc = self._map_http_error(exc)
                if exc.response.status_code < 500:
                    raise last_exc
            except TabdealAPIError as exc:
                last_exc = exc
                if exc.status_code and exc.status_code < 500 and exc.status_code != 502:
                    raise

            attempt += 1
            if attempt >= 3:
                break
            await asyncio.sleep((2**attempt) + random.random())

        if last_exc:
            raise last_exc
        raise TabdealAPIError("unknown tabdeal request failure", code="unknown")

    async def _signed_request(self, method: str, path: str, params: dict | None = None) -> Any:
        if not self.api_key or not self.api_secret:
            raise TabdealAPIError("Tabdeal credentials are missing", code="missing_credentials")
        payload = params.copy() if params else {}
        payload["timestamp"] = int(time.time() * 1000)
        query = urlencode(payload)
        signature = hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()
        payload["signature"] = signature
        return await self._request(method, path, params=payload, signed=True)

    def _map_http_error(self, exc: httpx.HTTPStatusError) -> TabdealAPIError:
        status_code = exc.response.status_code
        message = exc.response.text
        code: str | int | None = status_code
        try:
            data = exc.response.json()
            code = data.get("code", status_code)
            message = data.get("msg") or data.get("message") or message
        except ValueError:
            pass

        normalized = str(message).lower()
        if "symbol" in normalized or str(code) in {"1211", "1212"}:
            return TabdealAPIError("invalid symbol", code=code, status_code=status_code)
        if "access" in normalized or status_code == 403:
            return TabdealAPIError("access denied", code=code, status_code=status_code)
        if "balance" in normalized or str(code) == "1218":
            return TabdealAPIError("insufficient balance", code=code, status_code=status_code)
        if "precision" in normalized:
            return TabdealAPIError("invalid precision", code=code, status_code=status_code)
        if "quantity" in normalized or "qty" in normalized:
            return TabdealAPIError("invalid quantity", code=code, status_code=status_code)
        return TabdealAPIError(message, code=code, status_code=status_code)

    @staticmethod
    def _extract_symbols(payload: Any) -> list[dict]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            if isinstance(payload.get("symbols"), list):
                return payload["symbols"]
            if payload.get("symbol"):
                return [payload]
        return []

    @staticmethod
    def _to_decimal(value: str | float | Decimal, default_error: str = "invalid number") -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise TabdealAPIError(default_error, code="invalid_number") from exc

    @staticmethod
    def _decimal_to_str(value: Decimal) -> str:
        return format(value.normalize(), "f")

    @staticmethod
    def _quantize_to_step(value: Decimal, step: Decimal) -> Decimal:
        if step <= 0:
            return value
        multiplier = (value / step).to_integral_value(rounding=ROUND_DOWN)
        return multiplier * step
