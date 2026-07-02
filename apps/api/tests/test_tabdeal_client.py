import hmac
from decimal import Decimal
from urllib.parse import urlencode

from app.services.tabdeal_client import TabdealClient


def test_normalize_quantity_and_price() -> None:
    client = TabdealClient()
    rules = {"step_size": "0.01", "tick_size": "0.1", "symbol": "BTCUSDT", "quote_asset": "USDT", "base_asset": "BTC"}
    assert client.normalize_quantity(rules, "1.239") == "1.23"
    assert client.normalize_price(rules, "123.987") == "123.9"


def test_validate_order_uses_rules() -> None:
    client = TabdealClient()
    rules = {
        "symbol": "BTCUSDT",
        "quote_asset": "USDT",
        "base_asset": "BTC",
        "step_size": "0.01",
        "tick_size": "0.1",
        "min_qty": "0.10",
        "min_notional": "10",
    }
    result = client.validate_order(rules, "buy", "1.239", "15.45")
    assert result["quantity"] == "1.23"
    assert result["price"] == "15.4"
    assert result["side"] == "BUY"


def test_signed_query_uses_hmac_sha256() -> None:
    secret = b"demo-secret"
    payload = {"symbol": "BTCUSDT", "timestamp": 123456}
    query = urlencode(payload)
    signature = hmac.new(secret, query.encode("utf-8"), digestmod="sha256").hexdigest()
    assert len(signature) == 64
