from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import decrypt_secret
from app.db.models import AiDecision, ApiAccount, Position
from app.plugins.ai_engines.registry import ai_engine_registry
from app.services.account_service import get_active_api_account
from app.services.account_snapshot_service import build_account_snapshot
from app.services.indicator_engine import build_market_snapshot
from app.services.learning_memory_service import learning_memory_service
from app.services.market_data_service import MarketDataService
from app.services.notification_service import create_notification
from app.services.order_manager import OrderManager
from app.services.settings_service import settings_service
from app.services.system_log_service import create_system_log
from app.services.technical_guard import TechnicalGuardService


class TechnicalSummarySchema(BaseModel):
    trend: str
    momentum: str
    volume: str
    risk_level: str


class AiDecisionSchema(BaseModel):
    action: str
    confidence: int = Field(ge=0, le=100)
    reason: str
    entry_note: str
    entry_price: float | None = None
    breakout_price: float | None = None
    pullback_price: float | None = None
    take_profit_pct: float
    stop_loss_pct: float
    risk_warning: str
    technical_summary: TechnicalSummarySchema


class AiEngine:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def analyze(self, db: Session, symbol: str, strategy_name: str = "AI_TECHNICAL_GUARD") -> dict:
        account = get_active_api_account(db)
        ai_settings = settings_service.get_ai_engine_settings(db)
        engine_name = ai_settings.get("default_engine", "OPENAI").upper()
        engine_config = self._resolve_engine_config(account, ai_settings, engine_name)

        market_bundle = await MarketDataService().get_market_snapshot_bundle(symbol)
        market_snapshot = build_market_snapshot(market_bundle.__dict__)
        account_snapshot = await build_account_snapshot(db)
        guard_result = TechnicalGuardService().evaluate(market_snapshot, "BUY")
        learning_summary = learning_memory_service.get_summary(db, market_snapshot["symbol"], strategy_name)

        create_system_log(db, "INFO", "ai_signal", "Fetching market data for AI analysis.", {"symbol": market_snapshot["symbol"], "engine": engine_name})
        create_system_log(db, "INFO", "ai_signal", "Sending structured request to AI engine.", {"symbol": market_snapshot["symbol"], "engine": engine_name})

        prompt = self._build_prompt(market_snapshot, account_snapshot, learning_summary)
        decision_payload = await self._call_engine(engine_name, prompt, engine_config)

        record = AiDecision(
            api_account_id=account.id,
            symbol=market_snapshot["symbol"],
            action=decision_payload.action,
            confidence=decision_payload.confidence,
            reason=decision_payload.reason,
            entry_note=decision_payload.entry_note,
            entry_price=self._to_str(decision_payload.entry_price),
            breakout_price=self._to_str(decision_payload.breakout_price),
            pullback_price=self._to_str(decision_payload.pullback_price),
            take_profit_pct=self._to_str(decision_payload.take_profit_pct, "0"),
            stop_loss_pct=self._to_str(decision_payload.stop_loss_pct, "0"),
            risk_warning=decision_payload.risk_warning,
            technical_summary_json=decision_payload.technical_summary.model_dump(),
            market_snapshot_json=market_snapshot,
            account_snapshot_json=account_snapshot,
            guard_result_json=guard_result,
            risk_result_json=None,
            ai_engine_name=engine_name,
            strategy_name=strategy_name,
            learning_memory_json=learning_summary,
            executed=False,
            execution_order_id=None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        create_system_log(db, "INFO", "ai_signal", "AI decision received.", {"decision_id": record.id, "action": record.action, "engine": engine_name})
        create_notification(
            db,
            "ai_decision_created",
            "تصمیم AI جدید ثبت شد",
            f"AI برای {record.symbol} تصمیم {record.action} با confidence {record.confidence} ثبت کرد.",
            {"decision_id": record.id, "engine": engine_name},
            severity="AI",
        )
        return self.serialize(record)

    async def execute(self, db: Session, decision_id: int, prefer_real_execution: bool, confirm_token: str | None = None) -> dict:
        decision = db.get(AiDecision, decision_id)
        if not decision:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI decision not found.")
        if decision.action not in {"BUY_NOW", "BUY_AFTER_BREAKOUT", "WAIT_PULLBACK", "SELL"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This AI decision is not executable.")

        side = "SELL" if decision.action == "SELL" else "BUY"
        entry_price = decision.entry_price or decision.market_snapshot_json.get("analysis_close")
        payload = SimpleNamespace(
            symbol=decision.symbol,
            side=side,
            order_type="MARKET",
            quantity=None,
            price=str(entry_price) if entry_price else None,
            usdt_amount=None,
            prefer_real_execution=prefer_real_execution,
            idempotency_key=f"ai-{decision.id}-{side.lower()}",
            strategy_name=decision.strategy_name or "AI_TECHNICAL_GUARD",
            ai_engine_name=decision.ai_engine_name,
            entry_snapshot=decision.market_snapshot_json,
            decision_payload=self.serialize(decision),
        )
        if side == "BUY":
            payload.usdt_amount = "25"
        else:
            open_position = db.scalar(select(Position).where(Position.symbol == decision.symbol, Position.status == "OPEN").order_by(Position.opened_at.asc()))
            if not open_position:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No open position exists for AI SELL execution.")
            payload.quantity = open_position.quantity

        manager = OrderManager()
        if confirm_token:
            if not decision.execution_order_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This decision has no pending real order to confirm.")
            order = await manager.confirm_real_order(db, decision.execution_order_id, confirm_token)
            decision.executed = True
            db.add(decision)
            db.commit()
            db.refresh(decision)
            create_notification(db, "ai_buy_executed", "سفارش AI اجرا شد", f"سفارش AI برای {decision.symbol} اجرا شد.", {"decision_id": decision.id}, severity="AI")
            return {"decision": self.serialize(decision), "order": order}

        result = await manager.create_order(db, payload)
        decision.risk_result_json = result["preview"]["risk"]
        decision.guard_result_json = result["preview"]["technical_guard"]
        decision.execution_order_id = result["order"].id
        decision.executed = result["confirm_token"] is None
        db.add(decision)
        db.commit()
        db.refresh(decision)
        if result["preview"]["technical_guard"] and not result["preview"]["technical_guard"]["allowed"]:
            create_notification(db, "ai_buy_blocked", "خرید AI متوقف شد", "Technical Guard اجرای BUY را رد کرد.", {"decision_id": decision.id}, severity="AI")
        return {"decision": self.serialize(decision), "order": result["order"], "preview": result["preview"], "confirm_token": result["confirm_token"]}

    async def _call_engine(self, engine_name: str, prompt: str, engine_config: dict) -> AiDecisionSchema:
        try:
            response = await ai_engine_registry.get(engine_name).analyze({"prompt": prompt}, engine_config)
            return AiDecisionSchema.model_validate(response)
        except ValidationError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI engine returned invalid decision payload.") from exc
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI engine request failed.") from exc

    def _resolve_engine_config(self, account: ApiAccount, ai_settings: dict, engine_name: str) -> dict:
        if engine_name == "OPENAI":
            if not account.openai_api_key_encrypted:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active API account has no OpenAI API key.")
            return {"api_key": decrypt_secret(account.openai_api_key_encrypted), "model": account.openai_model}
        if engine_name == "OLLAMA":
            config = ai_settings.get("ollama", {})
            if not config.get("enabled"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ollama engine is disabled.")
            return {"base_url": config.get("base_url", self.settings.ollama_base_url), "model": config.get("model", self.settings.ollama_model)}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI engine not found.")

    @staticmethod
    def _build_prompt(market_snapshot: dict, account_snapshot: dict, learning_summary: dict | None) -> str:
        return (
            "You are a spot trading signal engine. Return JSON only.\n"
            "Decide using only validated market_snapshot and account_snapshot.\n"
            "If source_price_diff_pct > 1 then be cautious. If no clear edge, return HOLD.\n"
            "BUY_NOW only when RSI, MACD, EMA structure, volume_ratio, orderbook pressure and risk/reward are supportive.\n"
            "If price is near resistance and setup is good, return BUY_AFTER_BREAKOUT.\n"
            "If price is above support but stretched, return WAIT_PULLBACK.\n"
            "Spot only. No leverage.\n"
            "Output keys: action, confidence, reason, entry_note, entry_price, breakout_price, pullback_price, "
            "take_profit_pct, stop_loss_pct, risk_warning, technical_summary.\n"
            f"market_snapshot={json.dumps(market_snapshot, ensure_ascii=False)}\n"
            f"account_snapshot={json.dumps(account_snapshot, ensure_ascii=False)}\n"
            f"local_learning_memory={json.dumps(learning_summary or {}, ensure_ascii=False)}"
        )

    @staticmethod
    def _to_str(value: float | int | str | None, fallback: str | None = None) -> str | None:
        if value is None:
            return fallback
        return str(value)

    @staticmethod
    def serialize(item: AiDecision) -> dict:
        return {
            "id": item.id,
            "api_account_id": item.api_account_id,
            "symbol": item.symbol,
            "action": item.action,
            "confidence": item.confidence,
            "reason": item.reason,
            "entry_note": item.entry_note,
            "entry_price": item.entry_price,
            "breakout_price": item.breakout_price,
            "pullback_price": item.pullback_price,
            "take_profit_pct": item.take_profit_pct,
            "stop_loss_pct": item.stop_loss_pct,
            "risk_warning": item.risk_warning,
            "technical_summary_json": item.technical_summary_json,
            "market_snapshot_json": item.market_snapshot_json,
            "account_snapshot_json": item.account_snapshot_json,
            "guard_result_json": item.guard_result_json,
            "risk_result_json": item.risk_result_json,
            "ai_engine_name": item.ai_engine_name,
            "strategy_name": item.strategy_name,
            "learning_memory_json": item.learning_memory_json,
            "executed": item.executed,
            "execution_order_id": item.execution_order_id,
            "created_at": item.created_at,
        }
