from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AiDecision, BacktestRun, BotDecision, ScriptLog, ScriptRun, Trade


class ReportService:
    def get_summary(self, db: Session) -> dict:
        trades = db.scalars(select(Trade)).all()
        dry_run_pnl = 0.0
        real_pnl = 0.0
        for trade in trades:
            if trade.pnl is None:
                continue
            pnl = float(trade.pnl)
            if trade.mode.startswith("DRY_RUN"):
                dry_run_pnl += pnl
            else:
                real_pnl += pnl
        return {
            "trades_count": len(trades),
            "ai_decisions_count": len(db.scalars(select(AiDecision)).all()),
            "bot_decisions_count": len(db.scalars(select(BotDecision)).all()),
            "backtests_count": len(db.scalars(select(BacktestRun)).all()),
            "script_runs_count": len(db.scalars(select(ScriptRun)).all()),
            "dry_run_pnl": dry_run_pnl,
            "real_pnl": real_pnl,
        }

    def list_trades(self, db: Session, symbol: str | None = None, strategy: str | None = None, mode: str | None = None) -> list[Trade]:
        query = select(Trade).order_by(Trade.created_at.desc())
        if symbol:
            query = query.where(Trade.symbol == symbol.upper())
        if strategy:
            query = query.where(Trade.strategy_name == strategy)
        if mode:
            query = query.where(Trade.mode == mode.upper())
        return db.scalars(query).all()

    def list_ai_decisions(self, db: Session, symbol: str | None = None) -> list[AiDecision]:
        query = select(AiDecision).order_by(AiDecision.created_at.desc())
        if symbol:
            query = query.where(AiDecision.symbol == symbol.upper())
        return db.scalars(query).all()

    def list_bot_decisions(self, db: Session, symbol: str | None = None) -> list[BotDecision]:
        query = select(BotDecision).order_by(BotDecision.created_at.desc())
        if symbol:
            query = query.where(BotDecision.symbol == symbol.upper())
        return db.scalars(query).all()

    def list_backtests(self, db: Session, symbol: str | None = None, strategy: str | None = None) -> list[BacktestRun]:
        query = select(BacktestRun).order_by(BacktestRun.created_at.desc())
        if symbol:
            query = query.where(BacktestRun.symbol == symbol.upper())
        if strategy:
            query = query.where(BacktestRun.strategy_name == strategy.upper())
        return db.scalars(query).all()

    def pnl_by_symbol(self, db: Session) -> list[dict]:
        buckets: dict[str, dict[str, Any]] = {}
        for trade in db.scalars(select(Trade).where(Trade.pnl.is_not(None))).all():
            bucket = buckets.setdefault(trade.symbol, {"key": trade.symbol, "pnl": 0.0, "count": 0})
            bucket["pnl"] += float(trade.pnl or 0)
            bucket["count"] += 1
        return sorted(buckets.values(), key=lambda item: item["pnl"], reverse=True)

    def pnl_by_strategy(self, db: Session) -> list[dict]:
        buckets: dict[str, dict[str, Any]] = {}
        for trade in db.scalars(select(Trade).where(Trade.pnl.is_not(None))).all():
            key = trade.strategy_name or "unknown"
            bucket = buckets.setdefault(key, {"key": key, "pnl": 0.0, "count": 0})
            bucket["pnl"] += float(trade.pnl or 0)
            bucket["count"] += 1
        return sorted(buckets.values(), key=lambda item: item["pnl"], reverse=True)

    def chart_pnl_series(self, db: Session) -> list[dict]:
        running = 0.0
        points = []
        for trade in db.scalars(select(Trade).where(Trade.pnl.is_not(None)).order_by(Trade.created_at.asc())).all():
            running += float(trade.pnl or 0)
            points.append({"label": trade.created_at.isoformat(), "value": running})
        return points

    def export_csv(self, rows: list[Any], columns: list[tuple[str, str]]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([label for _, label in columns])
        for row in rows:
            writer.writerow([self._resolve_value(row, field) for field, _ in columns])
        return output.getvalue()

    def export_script_logs(self, db: Session) -> str:
        rows = db.scalars(select(ScriptLog).order_by(ScriptLog.created_at.desc())).all()
        return self.export_csv(
            rows,
            [
                ("id", "id"),
                ("script_run_id", "script_run_id"),
                ("stream", "stream"),
                ("line", "line"),
                ("created_at", "created_at"),
            ],
        )

    @staticmethod
    def _resolve_value(row: Any, field: str) -> Any:
        value = getattr(row, field)
        if isinstance(value, datetime):
            return value.isoformat()
        return value


report_service = ReportService()
