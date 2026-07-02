import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.models import Position
from app.services.indicator_engine import build_market_snapshot
from app.services.market_data_service import MarketDataService
from app.services.notification_service import create_notification
from app.services.order_manager import OrderManager
from app.services.system_log_service import create_system_log


class PositionMonitorService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> dict:
        if self._task and not self._task.done():
            return {"running": True}
        self._running = True
        self._task = asyncio.create_task(self._loop())
        return {"running": True}

    async def stop(self) -> dict:
        self._running = False
        if self._task:
            self._task.cancel()
        self._task = None
        return {"running": False}

    def status(self) -> dict:
        return {"running": self._running}

    async def _loop(self) -> None:
        while self._running:
            with SessionLocal() as db:
                positions = db.scalars(select(Position).where(Position.status == "OPEN")).all()
                for position in positions:
                    if not position.take_profit and not position.stop_loss:
                        continue
                    snapshot = build_market_snapshot((await MarketDataService().get_market_snapshot_bundle(position.symbol)).__dict__)
                    current = Decimal(snapshot["analysis_close"])
                    tp = Decimal(position.take_profit) if position.take_profit else None
                    sl = Decimal(position.stop_loss) if position.stop_loss else None
                    if tp is not None and current >= tp:
                        await self._close(db, position.id, "TP hit")
                    elif sl is not None and current <= sl:
                        await self._close(db, position.id, "SL hit")
            await asyncio.sleep(self.settings.position_monitor_interval_seconds)

    async def _close(self, db, position_id: int, reason: str) -> None:
        position = db.get(Position, position_id)
        if not position or position.status != "OPEN":
            return
        try:
            await OrderManager().close_position(db, position_id)
            create_notification(db, "tp_hit" if reason.startswith("TP") else "sl_hit", reason, f"{position.symbol}: {reason}", {"position_id": position_id})
            create_system_log(db, "INFO", "positions", "Position monitor closed position.", {"position_id": position_id, "reason": reason})
        except Exception as exc:  # noqa: BLE001
            create_notification(db, "close_failed", "بستن پوزیشن ناموفق بود", str(exc), {"position_id": position_id})
            create_system_log(db, "ERROR", "positions", "Position monitor close failed.", {"position_id": position_id, "error": str(exc)})


position_monitor_service = PositionMonitorService()
