from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LearningMemory, Position, TradeOutcome


class LearningMemoryService:
    def record_position_outcome(
        self,
        db: Session,
        position: Position,
        *,
        strategy_name: str = "manual_trading",
        ai_engine: str | None = None,
        entry_snapshot: dict | None = None,
        decision: dict | None = None,
        exit_reason: str = "manual_close",
    ) -> TradeOutcome:
        opened_at = position.opened_at or datetime.now(tz=UTC)
        closed_at = position.closed_at or datetime.now(tz=UTC)
        duration_seconds = max(int((closed_at - opened_at).total_seconds()), 0)
        outcome = TradeOutcome(
            symbol=position.symbol,
            strategy_name=strategy_name,
            ai_engine=ai_engine,
            entry_snapshot_json=entry_snapshot or {},
            decision_json=decision or {},
            exit_reason=exit_reason,
            pnl=position.pnl or "0",
            pnl_pct=position.pnl_pct or "0",
            duration_seconds=duration_seconds,
            was_successful=float(position.pnl or 0) > 0,
        )
        db.add(outcome)
        db.commit()
        db.refresh(outcome)
        self.rebuild_memory(db, position.symbol, strategy_name)
        return outcome

    def rebuild_memory(self, db: Session, symbol: str, strategy_name: str) -> LearningMemory:
        rows = db.scalars(
            select(TradeOutcome)
            .where(TradeOutcome.symbol == symbol, TradeOutcome.strategy_name == strategy_name)
            .order_by(TradeOutcome.created_at.desc())
        ).all()
        wins = [float(item.pnl or 0) for item in rows if item.was_successful]
        losses = [float(item.pnl or 0) for item in rows if not item.was_successful]
        exit_reasons = Counter(item.exit_reason for item in rows if not item.was_successful)
        stats = {
            "trades": len(rows),
            "win_rate": round((len(wins) / len(rows)) * 100, 2) if rows else 0,
            "avg_win": round(sum(wins) / len(wins), 8) if wins else 0,
            "avg_loss": round(sum(losses) / len(losses), 8) if losses else 0,
            "best_pnl": round(max([float(item.pnl or 0) for item in rows], default=0), 8),
            "worst_pnl": round(min([float(item.pnl or 0) for item in rows], default=0), 8),
        }
        lessons = {
            "common_failure_reasons": [{"reason": key, "count": value} for key, value in exit_reasons.most_common(5)],
            "recent_lessons": [
                {
                    "pnl": item.pnl,
                    "pnl_pct": item.pnl_pct,
                    "exit_reason": item.exit_reason,
                    "was_successful": item.was_successful,
                    "created_at": item.created_at.isoformat(),
                }
                for item in rows[:5]
            ],
            "best_setup": rows[0].decision_json if rows and rows[0].was_successful else {},
            "worst_setup": next((item.decision_json for item in rows if not item.was_successful), {}),
        }
        memory = db.scalar(select(LearningMemory).where(LearningMemory.symbol == symbol, LearningMemory.strategy_name == strategy_name))
        if not memory:
            memory = LearningMemory(symbol=symbol, strategy_name=strategy_name, stats_json=stats, lessons_json=lessons)
        else:
            memory.stats_json = stats
            memory.lessons_json = lessons
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    def get_summary(self, db: Session, symbol: str, strategy_name: str) -> dict | None:
        memory = db.scalar(select(LearningMemory).where(LearningMemory.symbol == symbol, LearningMemory.strategy_name == strategy_name))
        if not memory:
            return None
        return {
            "symbol": memory.symbol,
            "strategy_name": memory.strategy_name,
            "stats": memory.stats_json,
            "lessons": memory.lessons_json,
            "updated_at": memory.updated_at.isoformat(),
        }


learning_memory_service = LearningMemoryService()
