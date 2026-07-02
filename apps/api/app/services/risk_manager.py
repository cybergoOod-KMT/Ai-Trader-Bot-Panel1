from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ManualOrder, Position, Trade
from app.services.settings_service import settings_service


class RiskManager:
    def __init__(self) -> None:
        self.settings = get_settings()

    def evaluate_order(
        self,
        db: Session,
        api_account,
        symbol: str,
        side: str,
        rules: dict,
        quantity: str,
        estimated_value: str,
        account_payload: dict,
        prefer_real_execution: bool,
    ) -> dict:
        config = settings_service.get_risk_settings(db)
        reasons: list[str] = []
        qty_dec = Decimal(quantity)
        est_value = Decimal(estimated_value)

        if prefer_real_execution:
            mode = "REAL_PENDING_CONFIRM"
            if not self.settings.real_trading_enabled or config.get("real_trading_lock"):
                reasons.append("معامله واقعی در سطح سراسری غیرفعال یا قفل شده است.")
            if api_account.read_only:
                reasons.append("حساب فعال در حالت read-only است.")
            if not api_account.real_trading_allowed:
                reasons.append("برای این حساب اجازه معامله واقعی فعال نیست.")
        else:
            mode = "DRY_RUN"

        if config.get("pause_new_orders"):
            reasons.append("ثبت سفارش جدید به صورت اضطراری متوقف شده است.")
        if config.get("emergency_stop") or config.get("global_kill_switch"):
            reasons.append("Emergency stop فعال است.")

        min_notional = rules.get("min_notional")
        if min_notional and est_value < Decimal(str(min_notional)):
            reasons.append("ارزش سفارش کمتر از minNotional بازار است.")

        min_qty = rules.get("min_qty")
        if min_qty and qty_dec < Decimal(str(min_qty)):
            reasons.append("مقدار سفارش کمتر از minQty بازار است.")

        if est_value > Decimal(str(config["per_order_usdt"])):
            reasons.append("ارزش سفارش از سقف بودجه هر سفارش بیشتر است.")

        open_positions = db.scalars(select(Position).where(Position.status == "OPEN")).all()
        total_open_value = sum(Decimal(pos.entry_price) * Decimal(pos.quantity) for pos in open_positions)
        symbol_exposure = sum(
            Decimal(pos.entry_price) * Decimal(pos.quantity)
            for pos in open_positions
            if pos.symbol == symbol
        )
        if total_open_value + est_value > Decimal(str(config["max_total_budget_usdt"])):
            reasons.append("بودجه کل پوزیشن‌ها از سقف تعیین‌شده عبور می‌کند.")
        if total_open_value + est_value > Decimal(str(config.get("max_total_exposure_usdt", config["max_total_budget_usdt"]))):
            reasons.append("Total exposure exceeds allowed risk ceiling.")
        if symbol_exposure + est_value > Decimal(str(config.get("max_exposure_per_symbol_usdt", config["per_order_usdt"]))):
            reasons.append("انکشاف این نماد از سقف مجاز بیشتر می‌شود.")

        if side.upper() == "BUY" and len(open_positions) >= int(config["max_open_positions"]):
            reasons.append("حداکثر تعداد پوزیشن باز پر شده است.")

        today_start = datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = db.scalars(select(Trade).where(Trade.created_at >= today_start)).all()
        losses = Decimal("0")
        ordered_pnl_trades = sorted((trade for trade in trades_today if trade.pnl is not None), key=lambda item: item.created_at, reverse=True)
        consecutive_losses = 0
        for trade in trades_today:
            if trade.pnl and Decimal(trade.pnl) < 0:
                losses += abs(Decimal(trade.pnl))
        for trade in ordered_pnl_trades:
            if Decimal(trade.pnl or 0) < 0:
                consecutive_losses += 1
            else:
                break
        if losses > 0 and (losses / Decimal(str(config["max_total_budget_usdt"])) * Decimal("100")) > Decimal(str(config["max_daily_loss_pct"])):
            reasons.append("حداکثر ضرر روزانه رد شده است.")
        if losses > Decimal(str(config.get("max_loss_per_day_usdt", 0))):
            reasons.append("حداکثر ضرر روزانه دلاری رد شده است.")
        if consecutive_losses >= int(config.get("max_consecutive_losses", 3)):
            reasons.append("تعداد باخت‌های متوالی از حد مجاز بیشتر شده است.")

        recent_order = db.scalar(select(ManualOrder).where(ManualOrder.symbol == symbol).order_by(ManualOrder.created_at.desc()).limit(1))
        if recent_order and recent_order.created_at >= datetime.now(tz=UTC) - timedelta(seconds=int(config.get("symbol_cooldown_seconds", self.settings.risk_symbol_cooldown_seconds))):
            reasons.append("Cooldown این نماد هنوز تمام نشده است.")
        recent_loss_trade = next((trade for trade in ordered_pnl_trades if trade.symbol == symbol and Decimal(trade.pnl or 0) < 0), None)
        if recent_loss_trade and recent_loss_trade.created_at >= datetime.now(tz=UTC) - timedelta(seconds=int(config.get("cooldown_after_loss_seconds", 900))):
            reasons.append("Cooldown بعد از ضرر اخیر این نماد هنوز فعال است.")
        recent_api_error = db.scalar(select(ManualOrder).where(ManualOrder.status == "FAILED").order_by(ManualOrder.created_at.desc()).limit(1))
        if recent_api_error and recent_api_error.created_at >= datetime.now(tz=UTC) - timedelta(seconds=int(config.get("cooldown_after_api_error_seconds", 600))):
            reasons.append("Cooldown بعد از خطای API هنوز فعال است.")

        balances = account_payload.get("balances", [])
        balance_map = {item.get("asset"): Decimal(str(item.get("free") or item.get("availableBalance") or "0")) for item in balances}
        quote_asset = rules["quote_asset"]
        base_asset = rules["base_asset"]
        if side.upper() == "BUY":
            free_quote = balance_map.get(quote_asset, Decimal("0"))
            if free_quote - est_value < Decimal(str(config["min_usdt_reserve"])):
                reasons.append("ذخیره حداقل دارایی quote حفظ نمی‌شود.")
            if free_quote < est_value:
                reasons.append("موجودی کافی برای خرید وجود ندارد.")
        else:
            free_base = balance_map.get(base_asset, Decimal("0"))
            if free_base < qty_dec:
                reasons.append("موجودی پایه برای فروش کافی نیست.")

        return {
            "allowed": len(reasons) == 0,
            "reasons": reasons,
            "calculated_quantity": quantity,
            "estimated_value": f"{est_value:.8f}".rstrip("0").rstrip("."),
            "mode": mode,
        }
