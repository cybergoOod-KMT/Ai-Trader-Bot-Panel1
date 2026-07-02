from decimal import Decimal


def _fmt(value: float | Decimal) -> str:
    return f"{float(value):.8f}".rstrip("0").rstrip(".") or "0"


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    multiplier = 2 / (period + 1)
    ema_values = [values[0]]
    for price in values[1:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def _rsi(values: list[float], period: int = 14) -> float:
    if len(values) < period + 1:
        return 0.0
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _atr(candles: list[dict], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    trs = []
    for index, candle in enumerate(candles):
        high = float(candle["high"])
        low = float(candle["low"])
        prev_close = float(candles[index - 1]["close"]) if index > 0 else float(candle["close"])
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    relevant = trs[-period:]
    return sum(relevant) / len(relevant)


def build_market_snapshot(bundle: dict) -> dict:
    candles = bundle["candles"]
    closes = [float(item["close"]) for item in candles]
    highs = [float(item["high"]) for item in candles]
    lows = [float(item["low"]) for item in candles]
    volumes = [float(item["volume"]) for item in candles]

    ema9 = _ema(closes, 9)
    ema21 = _ema(closes, 21)
    ema50 = _ema(closes, 50)
    macd_fast = _ema(closes, 12)
    macd_slow = _ema(closes, 26)
    macd_line = [fast - slow for fast, slow in zip(macd_fast[-len(macd_slow):], macd_slow)]
    macd_signal_values = _ema(macd_line, 9) if macd_line else [0.0]
    macd_value = macd_line[-1] if macd_line else 0.0
    macd_signal = macd_signal_values[-1] if macd_signal_values else 0.0
    macd_histogram = macd_value - macd_signal

    best_bid = Decimal(bundle["orderbook"]["best_bid"] or "0")
    best_ask = Decimal(bundle["orderbook"]["best_ask"] or "0")
    bid_total = sum(Decimal(level["quantity"]) for level in bundle["orderbook"]["bids"])
    ask_total = sum(Decimal(level["quantity"]) for level in bundle["orderbook"]["asks"])
    orderbook_pressure = (bid_total / ask_total) if ask_total else Decimal("0")

    support_20 = min(lows[-20:]) if lows else 0.0
    resistance_20 = max(highs[-20:]) if highs else 0.0
    previous_volumes = volumes[-20:-1] if len(volumes) > 1 else [1.0]
    avg_previous_volume = sum(previous_volumes) / len(previous_volumes) if previous_volumes else 1.0
    volume_ratio = (volumes[-1] / avg_previous_volume) if avg_previous_volume else 0.0
    momentum_pct = ((closes[-1] - closes[0]) / closes[0] * 100) if closes and closes[0] else 0.0

    return {
        "symbol": bundle["symbol"],
        "source": bundle["source"],
        "timeframe": "1m_x_60",
        "lookback": "last_1_hour",
        "tabdeal_price": _fmt(bundle["tabdeal_price"]),
        "analysis_close": _fmt(bundle["analysis_close"]),
        "source_price_diff_pct": _fmt(bundle["source_price_diff_pct"]),
        "best_bid": _fmt(best_bid),
        "best_ask": _fmt(best_ask),
        "spread_pct": _fmt(bundle["orderbook"]["spread_pct"]),
        "rsi14": _fmt(_rsi(closes)),
        "ema9": _fmt(ema9[-1] if ema9 else 0.0),
        "ema21": _fmt(ema21[-1] if ema21 else 0.0),
        "ema50": _fmt(ema50[-1] if ema50 else 0.0),
        "macd": _fmt(macd_value),
        "macd_signal": _fmt(macd_signal),
        "macd_histogram": _fmt(macd_histogram),
        "atr14": _fmt(_atr(candles)),
        "support_20": _fmt(support_20),
        "resistance_20": _fmt(resistance_20),
        "volume_ratio": _fmt(volume_ratio),
        "momentum_pct_1h": _fmt(momentum_pct),
        "orderbook_pressure_bid_over_ask": _fmt(orderbook_pressure),
    }
