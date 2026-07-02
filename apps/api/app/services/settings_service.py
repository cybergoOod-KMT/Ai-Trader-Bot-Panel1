from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import SystemSetting


class SettingsService:
    def get(self, db: Session, key: str, default: dict | None = None) -> dict:
        row = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if row:
            return row.value_json or {}
        return default or {}

    def set(self, db: Session, key: str, value: dict) -> SystemSetting:
        row = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
        if not row:
            row = SystemSetting(key=key, value_json=value)
        else:
            row.value_json = value
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def get_risk_settings(self, db: Session) -> dict:
        defaults = self._risk_defaults()
        current = self.get(db, "risk_settings", defaults)
        merged = {**defaults, **current}
        return merged

    def _risk_defaults(self) -> dict:
        settings = get_settings()
        return {
            "max_total_budget_usdt": settings.risk_max_total_budget_usdt,
            "per_order_usdt": settings.risk_per_order_usdt,
            "min_usdt_reserve": settings.risk_min_usdt_reserve,
            "max_open_positions": settings.risk_max_open_positions,
            "max_daily_loss_pct": settings.risk_max_daily_loss_pct,
            "max_loss_per_trade_pct": 2.0,
            "max_loss_per_day_usdt": 250.0,
            "max_consecutive_losses": 3,
            "max_exposure_per_symbol_usdt": 250.0,
            "max_total_exposure_usdt": settings.risk_max_total_budget_usdt,
            "minimum_risk_reward": 1.5,
            "symbol_cooldown_seconds": settings.risk_symbol_cooldown_seconds,
            "cooldown_after_loss_seconds": 900,
            "cooldown_after_api_error_seconds": 600,
            "atr_position_size_multiplier": 1.0,
            "emergency_stop": False,
            "global_kill_switch": False,
            "pause_new_orders": False,
            "real_trading_lock": settings.real_trading_lock_default,
        }

    def get_ai_engine_settings(self, db: Session) -> dict:
        settings = get_settings()
        defaults = {
            "default_engine": "OPENAI",
            "openai": {"enabled": True, "model": settings.openai_default_model},
            "ollama": {"enabled": False, "base_url": settings.ollama_base_url, "model": settings.ollama_model},
        }
        return {**defaults, **self.get(db, "ai_engine_settings", defaults)}

    def get_strategy_settings(self, db: Session) -> dict:
        defaults = {"default_strategy": "AI_TECHNICAL_GUARD", "technical_guard_enabled": True}
        return {**defaults, **self.get(db, "strategy_settings", defaults)}

    def get_emergency_settings(self, db: Session) -> dict:
        defaults = {"real_trading_enabled_override": None, "close_all_real_preview_hash": None}
        return {**defaults, **self.get(db, "emergency_settings", defaults)}


settings_service = SettingsService()
