from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ManualOrder, Position, Trade
from app.services.account_service import get_active_credentials
from app.services.audit_service import create_audit_log
from app.services.indicator_engine import build_market_snapshot
from app.services.learning_memory_service import learning_memory_service
from app.services.market_data_service import MarketDataService
from app.services.notification_service import create_notification
from app.services.risk_manager import RiskManager
from app.services.system_log_service import create_system_log
from app.services.tabdeal_client import TabdealAPIError, TabdealClient
from app.services.technical_guard import TechnicalGuardService


class OrderManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.risk_manager = RiskManager()
        self.technical_guard = TechnicalGuardService()

    async def preview_order(self, db: Session, payload) -> dict:
        try:
            credentials = get_active_credentials(db)
            market_service = MarketDataService(TabdealClient(credentials.api_key, credentials.api_secret))
            symbol = market_service.normalize_symbol(payload.symbol)
            rules = await market_service.get_market_rules(symbol)
            bundle = await market_service.get_market_snapshot_bundle(symbol)
            snapshot = build_market_snapshot(bundle.__dict__)
            account_payload = await TabdealClient(credentials.api_key, credentials.api_secret).get_account()
        except TabdealAPIError as exc:
            raise self._translate_tabdeal_error(exc) from exc

        raw_price = payload.price or snapshot["analysis_close"]
        normalized_price = None
        if payload.order_type.upper() == "LIMIT":
            normalized_price = TabdealClient().normalize_price(rules, raw_price)
        working_price = Decimal(normalized_price or snapshot["analysis_close"])

        if payload.quantity:
            normalized_quantity = TabdealClient().normalize_quantity(rules, payload.quantity)
        elif payload.usdt_amount:
            qty = Decimal(payload.usdt_amount) / working_price
            normalized_quantity = TabdealClient().normalize_quantity(rules, str(qty))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quantity or usdt_amount is required.")

        estimated_value = Decimal(normalized_quantity) * working_price
        risk = self.risk_manager.evaluate_order(
            db=db,
            api_account=credentials.account,
            symbol=symbol,
            side=payload.side.upper(),
            rules=rules,
            quantity=normalized_quantity,
            estimated_value=str(estimated_value),
            account_payload=account_payload,
            prefer_real_execution=payload.prefer_real_execution,
        )
        guard = self.technical_guard.evaluate(snapshot, payload.side.upper()) if payload.side.upper() == "BUY" else None

        if not risk["allowed"]:
            create_notification(db, "risk_manager_blocked", "Risk Manager سفارش را متوقف کرد", "سفارش به دلیل قوانین ریسک رد شد.", {"symbol": symbol}, severity="WARNING")
        if guard and not guard["allowed"]:
            create_notification(db, "technical_guard_blocked", "Technical Guard خرید را متوقف کرد", "ورود خرید طبق وضعیت تکنیکال مجاز نبود.", {"symbol": symbol}, severity="WARNING")

        create_system_log(db, "INFO", "market_snapshot", "Market snapshot fetched.", {"symbol": symbol, "source": snapshot["source"]})
        create_system_log(db, "INFO", "risk", "Risk decision calculated.", {"symbol": symbol, "allowed": risk["allowed"]})
        if guard:
            create_system_log(db, "INFO", "technical_guard", "Technical guard decision calculated.", {"symbol": symbol, "allowed": guard["allowed"]})

        return {
            "symbol": symbol,
            "normalized_quantity": normalized_quantity,
            "normalized_price": normalized_price,
            "estimated_value": f"{estimated_value:.8f}".rstrip("0").rstrip("."),
            "market_snapshot": snapshot,
            "risk": risk,
            "technical_guard": guard,
            "api_account_id": credentials.account.id,
        }

    async def create_order(self, db: Session, payload, request: Request | None = None, actor_user=None) -> dict:
        idempotency_key = getattr(payload, "idempotency_key", None)
        if idempotency_key:
            existing = db.scalar(select(ManualOrder).where(ManualOrder.idempotency_key == idempotency_key).order_by(ManualOrder.id.desc()))
            if existing:
                return {"order": existing, "preview": existing.response_json.get("preview", {}), "confirm_token": None}

        preview = await self.preview_order(db, payload)
        risk = preview["risk"]
        guard = preview["technical_guard"]
        if not risk["allowed"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Risk Manager blocked this order.")
        if guard and not guard["allowed"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technical Guard blocked this BUY order.")

        order = ManualOrder(
            api_account_id=preview["api_account_id"],
            symbol=preview["symbol"],
            side=payload.side.upper(),
            order_type=payload.order_type.upper(),
            quantity=preview["normalized_quantity"],
            price=preview["normalized_price"],
            estimated_value=preview["estimated_value"],
            mode=risk["mode"],
            status="PENDING",
            response_json={"preview": preview},
            idempotency_key=idempotency_key,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        if risk["mode"] == "DRY_RUN":
            self._simulate_fill(
                db,
                order,
                preview["market_snapshot"],
                strategy_name=getattr(payload, "strategy_name", "manual_trading"),
                ai_engine_name=getattr(payload, "ai_engine_name", None),
                entry_snapshot=getattr(payload, "entry_snapshot", preview["market_snapshot"]),
                decision_payload=getattr(payload, "decision_payload", None),
            )
            create_notification(db, "dry_run_order_created", "سفارش Dry Run ثبت شد", f"{order.symbol} {order.side} به‌صورت شبیه‌سازی‌شده ثبت شد.", {"order_id": order.id}, severity="TRADE")
            create_system_log(db, "INFO", "manual_orders", "Dry-run order created.", {"order_id": order.id, "symbol": order.symbol})
            create_audit_log(db, "manual_order.create", "ManualOrder", str(order.id), actor_user=actor_user, after={"mode": order.mode, "status": order.status}, request=request)
            return {"order": order, "preview": preview, "confirm_token": None}

        confirm_token = secrets.token_urlsafe(24)
        order.status = "REAL_PENDING_CONFIRM"
        order.confirm_token_hash = self._hash_token(confirm_token)
        order.confirm_token_expires_at = datetime.now(tz=UTC) + timedelta(seconds=self.settings.real_confirm_token_ttl_seconds)
        db.add(order)
        db.commit()
        db.refresh(order)
        create_notification(db, "real_order_pending_confirmation", "سفارش واقعی در انتظار تأیید دوم است", f"سفارش {order.symbol} قبل از ارسال واقعی نیاز به تأیید دوم دارد.", {"order_id": order.id}, severity="TRADE")
        create_system_log(db, "INFO", "manual_orders", "Real order pending confirmation.", {"order_id": order.id})
        create_audit_log(db, "manual_order.preview_real", "ManualOrder", str(order.id), actor_user=actor_user, after={"mode": order.mode, "status": order.status}, request=request)
        return {"order": order, "preview": preview, "confirm_token": confirm_token}

    async def confirm_real_order(self, db: Session, order_id: int, confirm_token: str, request: Request | None = None, actor_user=None) -> ManualOrder:
        order = db.get(ManualOrder, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual order not found.")
        if order.mode != "REAL_PENDING_CONFIRM" or order.status != "REAL_PENDING_CONFIRM":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order is not waiting for real confirmation.")
        if not order.confirm_token_hash or not order.confirm_token_expires_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing confirmation token data.")
        if order.confirm_token_used_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation token was already used.")
        if order.confirm_token_expires_at < datetime.now(tz=UTC):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation token expired.")
        if self._hash_token(confirm_token) != order.confirm_token_hash:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid confirmation token.")
        if not self.settings.real_trading_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Real trading is globally disabled.")

        credentials = get_active_credentials(db)
        client = TabdealClient(credentials.api_key, credentials.api_secret)
        try:
            if order.order_type == "MARKET":
                response = await client.create_market_order(order.symbol, order.side, order.quantity)
            else:
                if not order.price:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit order requires a price.")
                response = await client.create_limit_order(order.symbol, order.side, order.quantity, order.price)
            order.exchange_order_id = str(response.get("orderId") or response.get("id") or "")
            order.response_json = response
            order.status = "REAL_SENT" if response.get("status") == "NEW" else "REAL_FILLED"
            order.confirm_token_used_at = datetime.now(tz=UTC)
            db.add(order)
            db.commit()
            db.refresh(order)
            if order.status == "REAL_FILLED":
                fill_price = str(response.get("price") or response.get("avgPrice") or order.price or "0")
                self._record_trade_and_position(db, order, fill_price, "REAL", "manual_trading", None, None, None)
            create_notification(db, "real_order_sent", "سفارش واقعی ارسال شد", f"سفارش {order.symbol} به Tabdeal ارسال شد.", {"order_id": order.id}, severity="TRADE")
            create_system_log(db, "INFO", "manual_orders", "Real order sent.", {"order_id": order.id, "symbol": order.symbol})
            create_audit_log(db, "manual_order.confirm_real", "ManualOrder", str(order.id), actor_user=actor_user, after={"status": order.status, "exchange_order_id": order.exchange_order_id}, request=request)
            return order
        except TabdealAPIError as exc:
            order.status = "FAILED"
            order.error_message = "Tabdeal request failed."
            db.add(order)
            db.commit()
            create_notification(db, "order_failed", "ارسال سفارش ناموفق بود", "ارسال سفارش به Tabdeal ناموفق بود.", {"order_id": order.id}, severity="ERROR")
            create_notification(db, "tabdeal_api_error", "خطای API تبدیل", "در ارتباط با Tabdeal خطا رخ داد.", {"order_id": order.id}, severity="ERROR")
            create_system_log(db, "ERROR", "manual_orders", "Real order failed.", {"order_id": order.id, "error_code": exc.code})
            create_audit_log(db, "manual_order.fail", "ManualOrder", str(order.id), actor_user=actor_user, after={"status": order.status}, request=request)
            raise self._translate_tabdeal_error(exc) from exc

    async def cancel_order(self, db: Session, order_id: int, request: Request | None = None, actor_user=None) -> ManualOrder:
        order = db.get(ManualOrder, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual order not found.")
        if order.mode == "DRY_RUN":
            order.status = "CANCELED"
            db.add(order)
            db.commit()
            db.refresh(order)
            create_system_log(db, "INFO", "manual_orders", "Dry-run order canceled.", {"order_id": order.id})
            create_audit_log(db, "manual_order.cancel", "ManualOrder", str(order.id), actor_user=actor_user, after={"status": order.status}, request=request)
            return order
        credentials = get_active_credentials(db)
        client = TabdealClient(credentials.api_key, credentials.api_secret)
        if order.exchange_order_id:
            response = await client.cancel_order(order.symbol, order.exchange_order_id)
            order.response_json = response
        order.status = "CANCELED"
        db.add(order)
        db.commit()
        db.refresh(order)
        create_system_log(db, "INFO", "manual_orders", "Real order canceled.", {"order_id": order.id})
        create_audit_log(db, "manual_order.cancel", "ManualOrder", str(order.id), actor_user=actor_user, after={"status": order.status}, request=request)
        return order

    async def close_position_preview(self, db: Session, position_id: int, generate_token: bool = True) -> dict:
        position = db.get(Position, position_id)
        if not position:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found.")
        market_service = MarketDataService()
        snapshot_bundle = await market_service.get_market_snapshot_bundle(position.symbol)
        snapshot = build_market_snapshot(snapshot_bundle.__dict__)
        estimated_close_price = snapshot["best_bid"] if Decimal(position.quantity) > 0 else snapshot["best_ask"]
        estimated_value = Decimal(position.quantity) * Decimal(estimated_close_price)
        mode = "DRY_RUN" if position.source.startswith("DRY_RUN") or not self.settings.real_trading_enabled else "REAL_PENDING_CONFIRM"
        token = None
        if mode == "REAL_PENDING_CONFIRM" and generate_token:
            token = secrets.token_urlsafe(24)
            position.current_price = estimated_close_price
            position.close_confirm_token_hash = self._hash_token(token)
            position.close_confirm_token_expires_at = datetime.now(tz=UTC) + timedelta(seconds=self.settings.real_confirm_token_ttl_seconds)
            position.close_confirm_token_used_at = None
            db.add(position)
            db.commit()
            db.refresh(position)
        return {
            "position_id": position.id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "estimated_close_price": estimated_close_price,
            "estimated_value": f"{estimated_value:.8f}".rstrip("0").rstrip("."),
            "mode": mode,
            "reasons": [],
            "confirm_token": token,
        }

    async def close_position(self, db: Session, position_id: int, confirm_token: str | None = None, request: Request | None = None, actor_user=None) -> Position:
        position = db.get(Position, position_id)
        if not position:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found.")
        preview = await self.close_position_preview(db, position_id, generate_token=False)
        if preview["mode"] == "REAL_PENDING_CONFIRM":
            if not confirm_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Real close requires confirmation token.")
            if not position.close_confirm_token_hash or not position.close_confirm_token_expires_at:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing close confirmation token.")
            if position.close_confirm_token_used_at is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Close confirmation token was already used.")
            if position.close_confirm_token_expires_at < datetime.now(tz=UTC):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Close confirmation token expired.")
            if self._hash_token(confirm_token) != position.close_confirm_token_hash:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid close confirmation token.")
            credentials = get_active_credentials(db)
            client = TabdealClient(credentials.api_key, credentials.api_secret)
            response = await client.create_market_order(position.symbol, "SELL", position.quantity)
            exit_price = str(response.get("price") or response.get("avgPrice") or preview["estimated_close_price"])
            position.close_confirm_token_used_at = datetime.now(tz=UTC)
            db.add(position)
            db.commit()
            db.refresh(position)
            self._close_position_record(db, position, exit_price, "REAL", "manual_close", None, None, "manual_close")
        else:
            self._close_position_record(db, position, preview["estimated_close_price"], "DRY_RUN", "manual_close", None, None, "manual_close")
        create_notification(db, "position_closed", "پوزیشن بسته شد", f"پوزیشن {position.symbol} بسته شد.", {"position_id": position.id}, severity="TRADE")
        create_system_log(db, "INFO", "positions", "Position closed.", {"position_id": position.id, "symbol": position.symbol})
        create_audit_log(db, "position.close", "Position", str(position.id), actor_user=actor_user, after={"status": position.status, "pnl": position.pnl}, request=request)
        return position

    def update_tpsl(self, db: Session, position_id: int, take_profit: str | None, stop_loss: str | None, request: Request | None = None, actor_user=None) -> Position:
        position = db.get(Position, position_id)
        if not position:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found.")
        before = {"take_profit": position.take_profit, "stop_loss": position.stop_loss}
        position.take_profit = take_profit
        position.stop_loss = stop_loss
        db.add(position)
        db.commit()
        db.refresh(position)
        create_audit_log(db, "position.update_tpsl", "Position", str(position.id), actor_user=actor_user, before=before, after={"take_profit": take_profit, "stop_loss": stop_loss}, request=request)
        return position

    def _simulate_fill(self, db: Session, order: ManualOrder, snapshot: dict, strategy_name: str, ai_engine_name: str | None, entry_snapshot: dict | None, decision_payload: dict | None) -> None:
        fill_price = order.price or snapshot["analysis_close"]
        order.status = "DRY_RUN_FILLED"
        order.response_json = {"simulated": True, "fill_price": fill_price, "source": snapshot["source"], "preview": order.response_json.get("preview")}
        db.add(order)
        db.commit()
        db.refresh(order)
        self._record_trade_and_position(db, order, fill_price, "DRY_RUN", strategy_name, ai_engine_name, entry_snapshot, decision_payload)

    def _record_trade_and_position(
        self,
        db: Session,
        order: ManualOrder,
        fill_price: str,
        mode: str,
        strategy_name: str,
        ai_engine_name: str | None,
        entry_snapshot: dict | None,
        decision_payload: dict | None,
    ) -> None:
        value = Decimal(order.quantity) * Decimal(fill_price)
        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            value=f"{value:.8f}".rstrip("0").rstrip("."),
            fee="0",
            mode=mode,
            source=mode,
            strategy_name=strategy_name,
            pnl=None,
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        base_asset = order.symbol[:-4]
        quote_asset = order.symbol[-4:]
        if order.side == "BUY":
            position = Position(
                symbol=order.symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                quantity=order.quantity,
                entry_price=fill_price,
                current_price=fill_price,
                take_profit=None,
                stop_loss=None,
                status="OPEN",
                source=mode,
                opened_by=strategy_name,
                pnl="0",
                pnl_pct="0",
            )
            db.add(position)
            db.commit()
            db.refresh(position)
            create_notification(db, "position_opened", "پوزیشن باز شد", f"پوزیشن {order.symbol} باز شد.", {"position_id": position.id}, severity="TRADE")
        else:
            open_position = db.scalar(select(Position).where(Position.symbol == order.symbol, Position.status == "OPEN").order_by(Position.opened_at.asc()))
            if open_position:
                self._close_position_record(db, open_position, fill_price, mode, strategy_name, ai_engine_name, entry_snapshot, "sell_execution", decision_payload)

    def _close_position_record(
        self,
        db: Session,
        position: Position,
        exit_price: str,
        mode: str,
        strategy_name: str,
        ai_engine_name: str | None,
        entry_snapshot: dict | None,
        exit_reason: str,
        decision_payload: dict | None = None,
    ) -> None:
        entry_value = Decimal(position.entry_price) * Decimal(position.quantity)
        exit_value = Decimal(exit_price) * Decimal(position.quantity)
        pnl = exit_value - entry_value
        pnl_pct = (pnl / entry_value * Decimal("100")) if entry_value else Decimal("0")
        position.current_price = exit_price
        position.status = "CLOSED"
        position.closed_at = datetime.now(tz=UTC)
        position.pnl = f"{pnl:.8f}".rstrip("0").rstrip(".")
        position.pnl_pct = f"{pnl_pct:.8f}".rstrip("0").rstrip(".")
        db.add(position)
        db.commit()
        db.refresh(position)

        closing_trade = Trade(
            symbol=position.symbol,
            side="SELL",
            quantity=position.quantity,
            price=exit_price,
            value=f"{exit_value:.8f}".rstrip("0").rstrip("."),
            fee="0",
            mode=mode,
            source="position_close",
            strategy_name=strategy_name,
            pnl=position.pnl,
        )
        db.add(closing_trade)
        db.commit()
        learning_memory_service.record_position_outcome(
            db,
            position,
            strategy_name=strategy_name,
            ai_engine=ai_engine_name,
            entry_snapshot=entry_snapshot,
            decision=decision_payload,
            exit_reason=exit_reason,
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _translate_tabdeal_error(exc: TabdealAPIError) -> HTTPException:
        status_code = status.HTTP_400_BAD_REQUEST
        if exc.status_code and exc.status_code >= 500:
            status_code = status.HTTP_502_BAD_GATEWAY
        if exc.code in {"network_unavailable", "timeout", "bad_gateway"}:
            status_code = status.HTTP_502_BAD_GATEWAY
        return HTTPException(status_code=status_code, detail="Tabdeal request failed.")
