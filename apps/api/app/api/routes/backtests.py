from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import BacktestRun, BacktestTrade, User
from app.schemas.backtests import BacktestEquityPoint, BacktestRunRequest, BacktestRunResponse, BacktestTradeResponse
from app.services.backtest_engine import backtest_engine

router = APIRouter(prefix="/backtests", tags=["backtests"])


def serialize_run(item: BacktestRun) -> BacktestRunResponse:
    return BacktestRunResponse(
        id=item.id,
        strategy_name=item.strategy_name,
        symbol=item.symbol,
        timeframe=item.timeframe,
        start_time=item.start_time,
        end_time=item.end_time,
        initial_balance=item.initial_balance,
        final_balance=item.final_balance,
        net_pnl=item.net_pnl,
        net_pnl_pct=item.net_pnl_pct,
        max_drawdown=item.max_drawdown,
        win_rate=item.win_rate,
        profit_factor=item.profit_factor,
        config_json=item.config_json,
        result_json=item.result_json,
        created_at=item.created_at,
    )


def serialize_trade(item: BacktestTrade) -> BacktestTradeResponse:
    return BacktestTradeResponse(
        id=item.id,
        backtest_run_id=item.backtest_run_id,
        symbol=item.symbol,
        side=item.side,
        entry_price=item.entry_price,
        exit_price=item.exit_price,
        quantity=item.quantity,
        pnl=item.pnl,
        pnl_pct=item.pnl_pct,
        opened_at=item.opened_at,
        closed_at=item.closed_at,
        reason=item.reason,
    )


@router.post("/run", response_model=BacktestRunResponse)
async def run_backtest(
    payload: BacktestRunRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BacktestRunResponse:
    return serialize_run(await backtest_engine.run(db, payload))


@router.get("", response_model=list[BacktestRunResponse])
def list_backtests(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BacktestRunResponse]:
    rows = db.scalars(select(BacktestRun).order_by(BacktestRun.created_at.desc())).all()
    return [serialize_run(item) for item in rows]


@router.get("/{backtest_id}", response_model=BacktestRunResponse)
def get_backtest(backtest_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BacktestRunResponse:
    item = db.get(BacktestRun, backtest_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest run not found.")
    return serialize_run(item)


@router.get("/{backtest_id}/trades", response_model=list[BacktestTradeResponse])
def get_backtest_trades(backtest_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BacktestTradeResponse]:
    rows = db.scalars(select(BacktestTrade).where(BacktestTrade.backtest_run_id == backtest_id).order_by(BacktestTrade.opened_at.asc())).all()
    return [serialize_trade(item) for item in rows]


@router.get("/{backtest_id}/equity", response_model=list[BacktestEquityPoint])
def get_backtest_equity(backtest_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BacktestEquityPoint]:
    item = db.get(BacktestRun, backtest_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest run not found.")
    points = item.result_json.get("equity_curve", [])
    return [BacktestEquityPoint(**point) for point in points]


@router.delete("/{backtest_id}")
def delete_backtest(backtest_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    item = db.get(BacktestRun, backtest_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest run not found.")
    for trade in db.scalars(select(BacktestTrade).where(BacktestTrade.backtest_run_id == backtest_id)).all():
        db.delete(trade)
    db.delete(item)
    db.commit()
    return {"success": True}
