from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.reports import PnlBucket, ReportSummaryResponse
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummaryResponse)
def get_summary(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReportSummaryResponse:
    return ReportSummaryResponse(**report_service.get_summary(db))


@router.get("/trades")
def get_trades(
    symbol: str | None = Query(default=None),
    strategy: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = report_service.list_trades(db, symbol=symbol, strategy=strategy, mode=mode)
    return [
        {
            "id": item.id,
            "symbol": item.symbol,
            "side": item.side,
            "quantity": item.quantity,
            "price": item.price,
            "value": item.value,
            "fee": item.fee,
            "mode": item.mode,
            "source": item.source,
            "strategy_name": item.strategy_name,
            "pnl": item.pnl,
            "created_at": item.created_at.isoformat(),
        }
        for item in rows
    ]


@router.get("/ai-decisions")
def get_ai_decisions(
    symbol: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = report_service.list_ai_decisions(db, symbol=symbol)
    return [
        {
            "id": item.id,
            "symbol": item.symbol,
            "action": item.action,
            "confidence": item.confidence,
            "reason": item.reason,
            "executed": item.executed,
            "created_at": item.created_at.isoformat(),
        }
        for item in rows
    ]


@router.get("/bot-decisions")
def get_bot_decisions(
    symbol: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = report_service.list_bot_decisions(db, symbol=symbol)
    return [
        {
            "id": item.id,
            "bot_run_id": item.bot_run_id,
            "symbol": item.symbol,
            "action": item.action,
            "confidence": item.confidence,
            "reason": item.reason,
            "executed": item.executed,
            "created_at": item.created_at.isoformat(),
        }
        for item in rows
    ]


@router.get("/backtests")
def get_backtests(
    symbol: str | None = Query(default=None),
    strategy: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = report_service.list_backtests(db, symbol=symbol, strategy=strategy)
    return [
        {
            "id": item.id,
            "strategy_name": item.strategy_name,
            "symbol": item.symbol,
            "timeframe": item.timeframe,
            "initial_balance": item.initial_balance,
            "final_balance": item.final_balance,
            "net_pnl": item.net_pnl,
            "net_pnl_pct": item.net_pnl_pct,
            "max_drawdown": item.max_drawdown,
            "win_rate": item.win_rate,
            "profit_factor": item.profit_factor,
            "created_at": item.created_at.isoformat(),
        }
        for item in rows
    ]


@router.get("/pnl-by-symbol", response_model=list[PnlBucket])
def get_pnl_by_symbol(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PnlBucket]:
    return [PnlBucket(**item) for item in report_service.pnl_by_symbol(db)]


@router.get("/pnl-by-strategy", response_model=list[PnlBucket])
def get_pnl_by_strategy(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PnlBucket]:
    return [PnlBucket(**item) for item in report_service.pnl_by_strategy(db)]


@router.get("/export/trades.csv")
def export_trades(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    csv_text = report_service.export_csv(
        report_service.list_trades(db),
        [
            ("id", "id"),
            ("symbol", "symbol"),
            ("side", "side"),
            ("quantity", "quantity"),
            ("price", "price"),
            ("value", "value"),
            ("fee", "fee"),
            ("mode", "mode"),
            ("source", "source"),
            ("strategy_name", "strategy_name"),
            ("pnl", "pnl"),
            ("created_at", "created_at"),
        ],
    )
    return Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=trades.csv"})


@router.get("/export/ai-decisions.csv")
def export_ai_decisions(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    csv_text = report_service.export_csv(
        report_service.list_ai_decisions(db),
        [
            ("id", "id"),
            ("symbol", "symbol"),
            ("action", "action"),
            ("confidence", "confidence"),
            ("reason", "reason"),
            ("executed", "executed"),
            ("created_at", "created_at"),
        ],
    )
    return Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=ai-decisions.csv"})


@router.get("/export/backtests.csv")
def export_backtests(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    csv_text = report_service.export_csv(
        report_service.list_backtests(db),
        [
            ("id", "id"),
            ("strategy_name", "strategy_name"),
            ("symbol", "symbol"),
            ("timeframe", "timeframe"),
            ("initial_balance", "initial_balance"),
            ("final_balance", "final_balance"),
            ("net_pnl", "net_pnl"),
            ("net_pnl_pct", "net_pnl_pct"),
            ("max_drawdown", "max_drawdown"),
            ("win_rate", "win_rate"),
            ("profit_factor", "profit_factor"),
            ("created_at", "created_at"),
        ],
    )
    return Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=backtests.csv"})


@router.get("/export/bot_decisions.csv")
def export_bot_decisions(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    csv_text = report_service.export_csv(
        report_service.list_bot_decisions(db),
        [
            ("id", "id"),
            ("bot_run_id", "bot_run_id"),
            ("symbol", "symbol"),
            ("action", "action"),
            ("confidence", "confidence"),
            ("reason", "reason"),
            ("executed", "executed"),
            ("created_at", "created_at"),
        ],
    )
    return Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=bot_decisions.csv"})


@router.get("/export/script_logs.csv")
def export_script_logs(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    csv_text = report_service.export_script_logs(db)
    return Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=script_logs.csv"})
