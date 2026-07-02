from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import engine
from app.services.bot_runner import bot_runner_service
from app.services.position_monitor import position_monitor_service
from app.services.script_runner import script_runner_service
from app.services.ws_manager import ws_manager


class HealthService:
    def basic(self) -> dict:
        return {"status": "ok"}

    def deep(self, db: Session) -> dict:
        settings = get_settings()
        db.execute(text("SELECT 1"))
        db_path = self._sqlite_path(settings.database_url)
        disk_target = db_path.parent if db_path else Path(".")
        usage = shutil.disk_usage(disk_target)
        return {
            "status": "ok",
            "components": {
                "database": {"ok": True, "url": "sqlite"},
                "api_service": {"ok": True},
                "bot_runner": {"ok": True, "active_tasks": len(bot_runner_service._tasks)},
                "position_monitor": position_monitor_service.status(),
                "script_runner": {"ok": True, "active_runs": len(script_runner_service._processes)},
                "websocket_manager": ws_manager.snapshot(),
                "disk": {
                    "ok": usage.free > 50 * 1024 * 1024,
                    "free_bytes": usage.free,
                    "total_bytes": usage.total,
                },
            },
        }

    @staticmethod
    def _sqlite_path(database_url: str) -> Path | None:
        if database_url.startswith("sqlite:///./"):
            return Path(database_url.replace("sqlite:///./", "./")).resolve()
        if database_url.startswith("sqlite:///"):
            return Path(database_url.replace("sqlite:///", "")).resolve()
        return None


health_service = HealthService()
