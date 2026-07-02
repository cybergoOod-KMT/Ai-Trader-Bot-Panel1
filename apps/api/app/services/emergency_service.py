from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import BotConfig, Position
from app.services.notification_service import create_notification
from app.services.order_manager import OrderManager
from app.services.settings_service import settings_service
from app.services.system_log_service import create_system_log


class EmergencyService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def stop_all_bots(self, db: Session) -> dict:
        rows = db.scalars(select(BotConfig).where(BotConfig.is_active.is_(True))).all()
        for row in rows:
            row.is_active = False
            db.add(row)
        db.commit()
        settings = settings_service.get_risk_settings(db)
        settings["pause_new_orders"] = True
        settings_service.set(db, "risk_settings", settings)
        create_notification(db, "bot_emergency_stop", "همه بات‌ها متوقف شدند", "تمام botهای فعال متوقف شدند.", {"count": len(rows)}, severity="WARNING")
        create_system_log(db, "WARNING", "emergency", "All bots stopped.", {"count": len(rows)})
        return {"stopped_bots": len(rows)}

    def pause_trading(self, db: Session) -> dict:
        settings = settings_service.get_risk_settings(db)
        settings["pause_new_orders"] = True
        settings_service.set(db, "risk_settings", settings)
        create_system_log(db, "WARNING", "emergency", "Trading paused.", None)
        return {"paused": True}

    def resume_trading(self, db: Session) -> dict:
        settings = settings_service.get_risk_settings(db)
        settings["pause_new_orders"] = False
        settings["emergency_stop"] = False
        settings_service.set(db, "risk_settings", settings)
        create_system_log(db, "INFO", "emergency", "Trading resumed.", None)
        return {"paused": False}

    def disable_real_trading(self, db: Session) -> dict:
        settings = settings_service.get_risk_settings(db)
        settings["real_trading_lock"] = True
        settings_service.set(db, "risk_settings", settings)
        create_notification(db, "real_trading_disabled", "معامله واقعی قفل شد", "مسیر اجرای REAL تا بازبینی بعدی قفل شد.", None, severity="WARNING")
        create_system_log(db, "WARNING", "emergency", "Real trading locked.", None)
        return {"real_trading_locked": True}

    async def close_all_dry_run(self, db: Session) -> dict:
        rows = db.scalars(select(Position).where(Position.status == "OPEN", Position.source.like("DRY_RUN%"))).all()
        closed = 0
        manager = OrderManager()
        for row in rows:
            await manager.close_position(db, row.id)
            closed += 1
        create_system_log(db, "WARNING", "emergency", "All dry-run positions closed.", {"count": closed})
        return {"closed_positions": closed}

    def close_all_real_preview(self, db: Session) -> dict:
        token = secrets.token_urlsafe(24)
        hashed = hashlib.sha256(token.encode("utf-8")).hexdigest()
        settings = settings_service.get_emergency_settings(db)
        settings["close_all_real_preview_hash"] = hashed
        settings["close_all_real_preview_expires_at"] = (datetime.now(tz=UTC) + timedelta(seconds=self.settings.real_confirm_token_ttl_seconds)).isoformat()
        settings_service.set(db, "emergency_settings", settings)
        create_system_log(db, "WARNING", "emergency", "Close-all-real preview created.", None)
        return {"confirm_token": token, "expires_in_seconds": self.settings.real_confirm_token_ttl_seconds}

    async def close_all_real_confirm(self, db: Session, confirm_token: str) -> dict:
        settings = settings_service.get_emergency_settings(db)
        expires_at = settings.get("close_all_real_preview_expires_at")
        expected = settings.get("close_all_real_preview_hash")
        if not expected or not expires_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active close-all-real preview.")
        if datetime.fromisoformat(expires_at) < datetime.now(tz=UTC):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Close-all-real preview expired.")
        if hashlib.sha256(confirm_token.encode("utf-8")).hexdigest() != expected:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid close-all-real confirmation token.")
        rows = db.scalars(select(Position).where(Position.status == "OPEN", ~Position.source.like("DRY_RUN%"))).all()
        manager = OrderManager()
        closed = 0
        for row in rows:
            await manager.close_position(db, row.id, confirm_token=confirm_token)
            closed += 1
        settings["close_all_real_preview_hash"] = None
        settings["close_all_real_preview_expires_at"] = None
        settings_service.set(db, "emergency_settings", settings)
        create_system_log(db, "WARNING", "emergency", "All real positions close confirmed.", {"count": closed})
        return {"closed_positions": closed}


emergency_service = EmergencyService()
