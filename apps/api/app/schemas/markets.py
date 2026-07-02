from pydantic import BaseModel


class MarketSearchItem(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    status: str


class MarketRulesResponse(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    price_precision: int
    quantity_precision: int
    min_qty: str | None
    step_size: str | None
    min_notional: str | None
    tick_size: str | None
    raw_filters: list[dict]


class OrderBookLevel(BaseModel):
    price: str
    quantity: str


class OrderBookResponse(BaseModel):
    symbol: str
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]
    best_bid: str | None
    best_ask: str | None
    spread_pct: str | None


class TradeTick(BaseModel):
    id: str | int | None = None
    price: str
    quantity: str
    timestamp: int | None = None
    is_buyer_maker: bool | None = None


class MarketSnapshotResponse(BaseModel):
    symbol: str
    source: str
    timeframe: str
    lookback: str
    tabdeal_price: str
    analysis_close: str
    source_price_diff_pct: str
    best_bid: str
    best_ask: str
    spread_pct: str
    rsi14: str
    ema9: str
    ema21: str
    ema50: str
    macd: str
    macd_signal: str
    macd_histogram: str
    atr14: str
    support_20: str
    resistance_20: str
    volume_ratio: str
    momentum_pct_1h: str
    orderbook_pressure_bid_over_ask: str
