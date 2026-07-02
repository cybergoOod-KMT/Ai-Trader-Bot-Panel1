import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.models import AiDecision, BotConfig, BotDecision, BotRun, Position, WatchTask
from app.services.account_snapshot_service import build_account_snapshot
from app.services.ai_engine import AiEngine
from app.services.indicator_engine import build_market_snapshot
from app.services.market_data_service import MarketDataService
from app.services.notification_service import create_notification
from app.services.order_manager import OrderManager
from app.services.risk_manager import RiskManager
from app.services.strategy_engine import StrategyEngine
from app.services.system_log_service import create_system_log
from app.services.technical_guard import TechnicalGuardService


class BotRunnerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._tasks: dict[int, asyncio.Task] = {}

    def orphan_existing_runs(self) -> None:
        with SessionLocal() as db:
            running_runs = db.scalars(select(BotRun).where(BotRun.status == "RUNNING")).all()
            for item in running_runs:
                item.status = "STOPPED"
                item.stopped_at = datetime.now(tz=UTC)
                item.error_message = "Bot run was orphaned after backend restart."
                db.add(item)
            active_configs = db.scalars(select(BotConfig).where(BotConfig.is_active.is_(True))).all()
            for config in active_configs:
                config.is_active = False
                db.add(config)
            db.commit()

    def list_status(self) -> dict:
        return {"active_runs": list(self._tasks.keys())}

    async def start_bot(self, db: Session, bot_id: int, confirm_token: str | None = None) -> dict:
        config = db.get(BotConfig, bot_id)
        if not config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot config not found.")
        running = db.scalar(select(BotRun).where(BotRun.bot_config_id == bot_id, BotRun.status == "RUNNING").limit(1))
        if running or any(task_id for task_id in self._tasks if task_id == (running.id if running else None)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bot is already running.")

        if config.mode == "REAL":
            if confirm_token is None:
                token = secrets.token_urlsafe(24)
                config.real_start_confirm_token_hash = self._hash_token(token)
                config.real_start_confirm_token_expires_at = datetime.now(tz=UTC) + timedelta(
                    seconds=self.settings.real_confirm_token_ttl_seconds
                )
                config.real_start_confirm_token_used_at = None
                db.add(config)
                db.commit()
                db.refresh(config)
                return {"status": "REAL_PENDING_CONFIRM", "confirm_token": token}
            if not config.real_start_confirm_token_hash or not config.real_start_confirm_token_expires_at:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing bot start confirmation token.")
            if config.real_start_confirm_token_used_at is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bot start token already used.")
            if config.real_start_confirm_token_expires_at < datetime.now(tz=UTC):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bot start token expired.")
            if self._hash_token(confirm_token) != config.real_start_confirm_token_hash:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bot start token.")
            config.real_start_confirm_token_used_at = datetime.now(tz=UTC)

        run = BotRun(bot_config_id=config.id, status="RUNNING", error_message=None)
        config.is_active = True
        config.api_error_count = 0
        db.add(run)
        db.add(config)
        db.commit()
        db.refresh(run)
        self._tasks[run.id] = asyncio.create_task(self._run_loop(run.id))
        create_notification(db, "bot_started", "ربات شروع شد", f"ربات {config.name} شروع شد.", {"bot_run_id": run.id})
        create_system_log(db, "INFO", "bots", "Bot started.", {"bot_run_id": run.id, "bot_config_id": config.id})
        return {"status": "RUNNING", "bot_run_id": run.id}

    async def stop_bot(self, db: Session, bot_id: int) -> dict:
        config = db.get(BotConfig, bot_id)
        if not config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot config not found.")
        run = db.scalar(select(BotRun).where(BotRun.bot_config_id == bot_id, BotRun.status == "RUNNING").order_by(BotRun.started_at.desc()))
        if run:
            run.status = "STOPPED"
            run.stopped_at = datetime.now(tz=UTC)
            db.add(run)
        config.is_active = False
        db.add(config)
        db.commit()
        task = self._tasks.pop(run.id, None) if run else None
        if task:
            task.cancel()
        create_notification(db, "bot_stopped", "ربات متوقف شد", f"ربات {config.name} متوقف شد.", {"bot_config_id": config.id})
        create_system_log(db, "INFO", "bots", "Bot stopped.", {"bot_config_id": config.id})
        return {"success": True}

    async def _run_loop(self, bot_run_id: int) -> None:
        try:
            while True:
                with SessionLocal() as db:
                    run = db.get(BotRun, bot_run_id)
                    if not run or run.status != "RUNNING":
                        return
                    config = db.get(BotConfig, run.bot_config_id)
                    if not config or not config.is_active:
                        return
                    await self._scan_symbols(db, run, config)
                    await self._evaluate_watch_tasks(db, run, config)
                await asyncio.sleep(self.settings.bot_scan_interval_seconds)
        except asyncio.CancelledError:
            return
        except Exception as exc:  # noqa: BLE001
            with SessionLocal() as db:
                run = db.get(BotRun, bot_run_id)
                if run:
                    run.status = "ERROR"
                    run.error_message = str(exc)
                    run.stopped_at = datetime.now(tz=UTC)
                    db.add(run)
                    config = db.get(BotConfig, run.bot_config_id)
                    if config:
                        config.is_active = False
                        db.add(config)
                    db.commit()
                    create_notification(db, "bot_error", "ربات با خطا متوقف شد", str(exc), {"bot_run_id": bot_run_id})
                    create_system_log(db, "ERROR", "bots", "Bot error.", {"bot_run_id": bot_run_id, "error": str(exc)})
            self._tasks.pop(bot_run_id, None)

    async def _scan_symbols(self, db: Session, run: BotRun, config: BotConfig) -> None:
        for raw_symbol in config.symbols_json:
            symbol = MarketDataService.normalize_symbol(raw_symbol)
            market_bundle = await MarketDataService().get_market_snapshot_bundle(symbol)
            market_snapshot = build_market_snapshot(market_bundle.__dict__)
            account_snapshot = await build_account_snapshot(db)
            open_positions = [
                {
                    "symbol": item.symbol,
                    "quantity": item.quantity,
                    "entry_price": item.entry_price,
                }
                for item in db.scalars(select(Position).where(Position.status == "OPEN")).all()
            ]
            strategy_decision = StrategyEngine().analyze(
                config.strategy_name,
                {"per_order_usdt": config.per_order_usdt},
                market_snapshot,
                account_snapshot,
                open_positions,
            )
            guard_result = TechnicalGuardService().evaluate(market_snapshot, "BUY")
            ai_record = None
            final_action = strategy_decision["action"]
            confidence = int(strategy_decision["confidence"])
            reason = strategy_decision["reason"]
            if config.strategy_name.upper() == "AI_TECHNICAL_GUARD":
                ai_record = await AiEngine().analyze(db, symbol, config.strategy_name)
                final_action = ai_record["action"]
                confidence = int(ai_record["confidence"])
                reason = ai_record["reason"]

            risk_result = {
                "allowed": True,
                "reasons": [],
                "mode": config.mode,
            }
            executed = False
            if final_action in {"BUY", "BUY_NOW"} and confidence >= config.min_ai_confidence:
                if config.technical_guard_enabled and not guard_result["allowed"]:
                    create_notification(db, "strategy_blocked_by_risk", "خرید ربات بلاک شد", "Technical Guard اجازه BUY نداد.", {"symbol": symbol})
                else:
                    try:
                        payload = SimpleNamespace(
                            symbol=symbol,
                            side="BUY",
                            order_type="MARKET",
                            quantity=None,
                            price=None,
                            usdt_amount=str(config.per_order_usdt),
                            prefer_real_execution=config.mode == "REAL",
                            idempotency_key=f"bot-{run.id}-{symbol}-{datetime.now(tz=UTC).strftime('%Y%m%d%H%M')}",
                            strategy_name=config.strategy_name,
                            ai_engine_name=config.ai_engine_name,
                            entry_snapshot=market_snapshot,
                            decision_payload=ai_record,
                        )
                        result = await OrderManager().create_order(db, payload)
                        risk_result = result["preview"]["risk"]
                        executed = risk_result["allowed"] and (result["confirm_token"] is None)
                    except Exception as exc:  # noqa: BLE001
                        config.api_error_count += 1
                        db.add(config)
                        db.commit()
                        if config.api_error_count >= self.settings.bot_api_error_threshold:
                            run.status = "ERROR"
                            run.error_message = f"API error threshold reached: {exc}"
                            run.stopped_at = datetime.now(tz=UTC)
                            config.is_active = False
                            db.add(run)
                            db.add(config)
                            db.commit()
                        create_notification(db, "bot_error", "ربات خطای API گرفت", str(exc), {"symbol": symbol, "bot_run_id": run.id})
            elif final_action in {"WATCH", "BUY_AFTER_BREAKOUT", "WAIT_PULLBACK"}:
                self._create_watch_task(db, run.id, symbol, final_action, market_snapshot, reason)

            bot_decision = BotDecision(
                bot_run_id=run.id,
                symbol=symbol,
                action=final_action,
                confidence=confidence,
                reason=reason,
                market_snapshot_json=market_snapshot,
                ai_decision_id=ai_record["id"] if ai_record else None,
                guard_result_json=guard_result,
                risk_result_json=risk_result,
                executed=executed,
            )
            db.add(bot_decision)
            db.commit()
            db.refresh(bot_decision)
            create_notification(db, "strategy_decision", "تصمیم استراتژی ثبت شد", f"{symbol}: {final_action}", {"bot_decision_id": bot_decision.id})
            create_system_log(db, "INFO", "bots", "Bot decision stored.", {"bot_run_id": run.id, "symbol": symbol, "action": final_action})

    async def _evaluate_watch_tasks(self, db: Session, run: BotRun, config: BotConfig) -> None:
        tasks = db.scalars(select(WatchTask).where(WatchTask.bot_run_id == run.id, WatchTask.status == "WATCHING")).all()
        for task in tasks:
            market_snapshot = build_market_snapshot((await MarketDataService().get_market_snapshot_bundle(task.symbol)).__dict__)
            price = Decimal(market_snapshot["analysis_close"])
            volume_ratio = Decimal(market_snapshot["volume_ratio"])
            pressure = Decimal(market_snapshot["orderbook_pressure_bid_over_ask"])
            trigger = Decimal(task.trigger_price)
            invalidation = Decimal(task.invalidation_price) if task.invalidation_price else None
            triggered = False
            if task.type == "BREAKOUT":
                triggered = price > trigger and volume_ratio >= Decimal("1.5") and pressure >= Decimal("1.2")
            if task.type == "PULLBACK":
                triggered = price <= trigger and pressure >= Decimal("1.0")
            if triggered:
                task.status = "TRIGGERED"
                db.add(task)
                db.commit()
                create_notification(db, "watch_task_triggered", "واچ تریگر شد", f"{task.symbol} watch task triggered.", {"watch_task_id": task.id})
                payload = SimpleNamespace(
                    symbol=task.symbol,
                    side="BUY",
                    order_type="MARKET",
                    quantity=None,
                    price=None,
                    usdt_amount=str(config.per_order_usdt),
                    prefer_real_execution=config.mode == "REAL",
                    idempotency_key=f"watch-{task.id}-{datetime.now(tz=UTC).strftime('%Y%m%d%H%M')}",
                    strategy_name=config.strategy_name,
                    ai_engine_name=config.ai_engine_name,
                    entry_snapshot=market_snapshot,
                )
                try:
                    await OrderManager().create_order(db, payload)
                except Exception:
                    pass
            elif invalidation is not None and ((task.type == "BREAKOUT" and price < invalidation) or (task.type == "PULLBACK" and price < invalidation)):
                task.status = "EXPIRED"
                db.add(task)
                db.commit()
                create_notification(db, "watch_task_expired", "واچ منقضی شد", f"{task.symbol} watch task expired.", {"watch_task_id": task.id})

    def _create_watch_task(self, db: Session, bot_run_id: int, symbol: str, action: str, market_snapshot: dict, reason: str) -> None:
        watch_type = "BREAKOUT" if action in {"WATCH", "BUY_AFTER_BREAKOUT"} else "PULLBACK"
        trigger = market_snapshot["resistance_20"] if watch_type == "BREAKOUT" else market_snapshot["support_20"]
        invalidation = market_snapshot["ema21"] if watch_type == "BREAKOUT" else market_snapshot["support_20"]
        existing = db.scalar(select(WatchTask).where(WatchTask.bot_run_id == bot_run_id, WatchTask.symbol == symbol, WatchTask.status == "WATCHING"))
        if existing:
            return
        task = WatchTask(
            bot_run_id=bot_run_id,
            symbol=symbol,
            type=watch_type,
            trigger_price=str(trigger),
            invalidation_price=str(invalidation),
            status="WATCHING",
            reason=reason,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        create_notification(db, "watch_task_created", "واچ جدید ساخته شد", f"Watch task for {symbol} created.", {"watch_task_id": task.id})

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


bot_runner_service = BotRunnerService()
