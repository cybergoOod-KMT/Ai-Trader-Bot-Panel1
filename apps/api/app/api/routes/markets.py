from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.markets import MarketRulesResponse, MarketSearchItem, MarketSnapshotResponse, OrderBookResponse, TradeTick
from app.services.indicator_engine import build_market_snapshot
from app.services.market_data_service import MarketDataService
from app.services.system_log_service import create_system_log
from app.services.tabdeal_client import TabdealAPIError

router = APIRouter(prefix="/markets", tags=["markets"])


def _translate_tabdeal_error(exc: TabdealAPIError) -> HTTPException:
    status_code = 502 if exc.status_code and exc.status_code >= 500 else 400
    if exc.code in {"network_unavailable", "timeout", "bad_gateway"}:
        status_code = 502
    return HTTPException(status_code=status_code, detail=str(exc))


@router.get("/search", response_model=list[MarketSearchItem])
async def search_markets(
    query: str = Query(default=""),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MarketSearchItem]:
    service = MarketDataService()
    try:
        results = await service.search_markets(query)
    except TabdealAPIError as exc:
        raise _translate_tabdeal_error(exc) from exc
    create_system_log(db, "INFO", "markets", "Market search executed.", {"query": query, "count": len(results)})
    return [MarketSearchItem(**item) for item in results]


@router.get("/{symbol}")
async def get_market(
    symbol: str,
    _: User = Depends(get_current_user),
) -> dict:
    service = MarketDataService()
    try:
        rules = await service.get_market_rules(symbol)
    except TabdealAPIError as exc:
        raise _translate_tabdeal_error(exc) from exc
    return rules


@router.get("/{symbol}/snapshot", response_model=MarketSnapshotResponse)
async def get_market_snapshot(
    symbol: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarketSnapshotResponse:
    service = MarketDataService()
    try:
        bundle = await service.get_market_snapshot_bundle(symbol)
    except TabdealAPIError as exc:
        raise _translate_tabdeal_error(exc) from exc
    snapshot = build_market_snapshot(bundle.__dict__)
    create_system_log(db, "INFO", "markets", "Market snapshot fetched.", {"symbol": snapshot["symbol"], "source": snapshot["source"]})
    return MarketSnapshotResponse(**snapshot)


@router.get("/{symbol}/rules", response_model=MarketRulesResponse)
async def get_market_rules(
    symbol: str,
    _: User = Depends(get_current_user),
) -> MarketRulesResponse:
    service = MarketDataService()
    try:
        rules = await service.get_market_rules(symbol)
    except TabdealAPIError as exc:
        raise _translate_tabdeal_error(exc) from exc
    return MarketRulesResponse(
        symbol=rules["symbol"],
        base_asset=rules["base_asset"],
        quote_asset=rules["quote_asset"],
        price_precision=rules["price_precision"],
        quantity_precision=rules["quantity_precision"],
        min_qty=rules["min_qty"],
        step_size=rules["step_size"],
        min_notional=rules["min_notional"],
        tick_size=rules["tick_size"],
        raw_filters=rules["filters"],
    )


@router.get("/{symbol}/orderbook", response_model=OrderBookResponse)
async def get_market_orderbook(
    symbol: str,
    _: User = Depends(get_current_user),
) -> OrderBookResponse:
    service = MarketDataService()
    try:
        book = await service.get_orderbook(symbol, limit=20)
    except TabdealAPIError as exc:
        raise _translate_tabdeal_error(exc) from exc
    return OrderBookResponse(**book)


@router.get("/{symbol}/recent-trades", response_model=list[TradeTick])
async def get_market_recent_trades(
    symbol: str,
    _: User = Depends(get_current_user),
) -> list[TradeTick]:
    service = MarketDataService()
    try:
        trades = await service.get_recent_trades(symbol, limit=100)
    except TabdealAPIError as exc:
        raise _translate_tabdeal_error(exc) from exc
    return [TradeTick(**item) for item in trades]
