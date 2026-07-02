from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import BacktestRun, BacktestTrade
from app.services.indicator_engine import build_market_snapshot
from app.services.notification_service import create_notification
from app.services.strategy_engine import StrategyEngine
from app.services.system_log_service import create_system_log
from app.services.technical_guard import TechnicalGuardService


def _fmt_decimal(value: Decimal) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".") or "0"


class BacktestEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.strategy_engine = StrategyEngine()
        self.technical_guard = TechnicalGuardService()
        self.import_root = Path("./data/imports")
        self.import_root.mkdir(parents=True, exist_ok=True)

    async def import_csv(self, upload_bytes: bytes, filename: str) -> dict:
        if len(upload_bytes) > 2 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="CSV upload is too large.")
        text = upload_bytes.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
        expected = {"timestamp", "open", "high", "low", "close", "volume"}
        if not rows:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty.")
        if set(rows[0].keys() or []) != expected:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV columns must be timestamp, open, high, low, close, volume.")
        validated_rows = []
        for row in rows:
            try:
                timestamp = self._parse_timestamp(row["timestamp"])
                validated_rows.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid CSV row: {exc}") from exc
        dataset_id = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S%f")
        path = self.import_root / f"{dataset_id}.csv"
        path.write_text(text, encoding="utf-8")
        return {"dataset_id": dataset_id, "rows": len(validated_rows), "symbol_hint": filename.rsplit(".", 1)[0] or None}

    async def run(self, db: Session, payload) -> BacktestRun:
        symbol = payload.symbol.upper()
        candles = await self._load_candles(symbol, payload.timeframe, payload.start_time, payload.end_time, payload.csv_dataset_id)
        if len(candles) < 60:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least 60 candles are required for backtest analysis.")

        initial_balance = Decimal(str(payload.initial_balance))
        cash = initial_balance
        open_position: dict[str, Any] | None = None
        trades: list[dict] = []
        equity_curve: list[dict] = []
        peak_equity = initial_balance
        max_drawdown = Decimal("0")

        for index in range(59, len(candles)):
            window = candles[max(0, index - 59) : index + 1]
            current = candles[index]
            snapshot = self._snapshot_from_candles(symbol, window)
            open_positions = [open_position] if open_position else []
            decision = self._analyze_strategy(payload.strategy_name, payload.config_json, snapshot, open_positions)

            current_price = Decimal(str(current["close"]))
            equity = cash if not open_position else cash + (Decimal(open_position["quantity"]) * current_price)
            peak_equity = max(peak_equity, equity)
            if peak_equity > 0:
                max_drawdown = max(max_drawdown, ((peak_equity - equity) / peak_equity) * Decimal("100"))
            equity_curve.append({"timestamp": datetime.fromtimestamp(current["close_time"] / 1000, tz=UTC).isoformat(), "equity": float(equity), "drawdown_pct": float(max_drawdown)})

            if open_position:
                take_profit_price = Decimal(open_position["take_profit_price"])
                stop_loss_price = Decimal(open_position["stop_loss_price"])
                exit_reason = None
                exit_price = current_price
                if current_price >= take_profit_price:
                    exit_reason = "TAKE_PROFIT"
                elif current_price <= stop_loss_price:
                    exit_reason = "STOP_LOSS"
                elif decision["action"] == "SELL":
                    exit_reason = "STRATEGY_SELL"
                if exit_reason:
                    entry_value = Decimal(open_position["entry_price"]) * Decimal(open_position["quantity"])
                    exit_value = exit_price * Decimal(open_position["quantity"])
                    pnl = exit_value - entry_value
                    pnl_pct = (pnl / entry_value * Decimal("100")) if entry_value else Decimal("0")
                    cash = exit_value
                    trades.append(
                        {
                            "symbol": symbol,
                            "side": "BUY",
                            "entry_price": _fmt_decimal(Decimal(open_position["entry_price"])),
                            "exit_price": _fmt_decimal(exit_price),
                            "quantity": _fmt_decimal(Decimal(open_position["quantity"])),
                            "pnl": _fmt_decimal(pnl),
                            "pnl_pct": _fmt_decimal(pnl_pct),
                            "opened_at": open_position["opened_at"],
                            "closed_at": datetime.fromtimestamp(current["close_time"] / 1000, tz=UTC),
                            "reason": exit_reason,
                        }
                    )
                    open_position = None
                    continue

            if open_position:
                continue

            if decision["action"] != "BUY":
                continue

            entry_price = current_price
            quantity = cash / entry_price if entry_price else Decimal("0")
            if quantity <= 0:
                continue
            tp_pct = Decimal(str(decision.get("take_profit_pct") or 2))
            sl_pct = Decimal(str(decision.get("stop_loss_pct") or 1))
            cash = Decimal("0")
            open_position = {
                "entry_price": _fmt_decimal(entry_price),
                "quantity": _fmt_decimal(quantity),
                "opened_at": datetime.fromtimestamp(current["close_time"] / 1000, tz=UTC),
                "take_profit_price": _fmt_decimal(entry_price * (Decimal("1") + (tp_pct / Decimal("100")))),
                "stop_loss_price": _fmt_decimal(entry_price * (Decimal("1") - (sl_pct / Decimal("100")))),
            }

        final_balance = cash
        if open_position:
            last_close = Decimal(str(candles[-1]["close"]))
            final_balance = Decimal(open_position["quantity"]) * last_close
            entry_value = Decimal(open_position["entry_price"]) * Decimal(open_position["quantity"])
            pnl = final_balance - entry_value
            pnl_pct = (pnl / entry_value * Decimal("100")) if entry_value else Decimal("0")
            trades.append(
                {
                    "symbol": symbol,
                    "side": "BUY",
                    "entry_price": open_position["entry_price"],
                    "exit_price": _fmt_decimal(last_close),
                    "quantity": open_position["quantity"],
                    "pnl": _fmt_decimal(pnl),
                    "pnl_pct": _fmt_decimal(pnl_pct),
                    "opened_at": open_position["opened_at"],
                    "closed_at": datetime.fromtimestamp(candles[-1]["close_time"] / 1000, tz=UTC),
                    "reason": "FORCED_END",
                }
            )

        wins = [Decimal(item["pnl"]) for item in trades if Decimal(item["pnl"]) > 0]
        losses = [abs(Decimal(item["pnl"])) for item in trades if Decimal(item["pnl"]) <= 0]
        net_pnl = final_balance - initial_balance
        win_rate = (Decimal(len(wins)) / Decimal(len(trades)) * Decimal("100")) if trades else Decimal("0")
        gross_profit = sum(wins, Decimal("0"))
        gross_loss = sum(losses, Decimal("0"))
        profit_factor = gross_profit / gross_loss if gross_loss else gross_profit

        run = BacktestRun(
            strategy_name=payload.strategy_name.upper(),
            symbol=symbol,
            timeframe=payload.timeframe,
            start_time=payload.start_time,
            end_time=payload.end_time,
            initial_balance=_fmt_decimal(initial_balance),
            final_balance=_fmt_decimal(final_balance),
            net_pnl=_fmt_decimal(net_pnl),
            net_pnl_pct=_fmt_decimal((net_pnl / initial_balance * Decimal("100")) if initial_balance else Decimal("0")),
            max_drawdown=_fmt_decimal(max_drawdown),
            win_rate=_fmt_decimal(win_rate),
            profit_factor=_fmt_decimal(profit_factor),
            config_json=payload.config_json,
            result_json={
                "total_trades": len(trades),
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "average_win": _fmt_decimal((gross_profit / Decimal(len(wins))) if wins else Decimal("0")),
                "average_loss": _fmt_decimal((gross_loss / Decimal(len(losses))) if losses else Decimal("0")),
                "equity_curve": equity_curve,
            },
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        for item in trades:
            db.add(BacktestTrade(backtest_run_id=run.id, **item))
        db.commit()
        create_system_log(db, "INFO", "backtests", "Backtest completed.", {"backtest_run_id": run.id, "symbol": symbol, "strategy": payload.strategy_name.upper()})
        create_notification(db, "BACKTEST", "بک‌تست کامل شد", f"بک‌تست {symbol} با استراتژی {payload.strategy_name.upper()} کامل شد.", {"backtest_run_id": run.id}, severity="SUCCESS")
        return run

    async def _load_candles(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime, csv_dataset_id: str | None) -> list[dict]:
        if csv_dataset_id:
            return self._load_candles_from_csv(csv_dataset_id)

        params = {
            "symbol": symbol,
            "interval": timeframe,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
            "limit": 1000,
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(self.settings.binance_klines_url, params=params)
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Binance klines request timed out. Use CSV import fallback or retry later.") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Binance klines request failed. Use CSV import fallback or retry later.") from exc
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Binance klines request failed.")
        data = response.json()
        return [
            {
                "open_time": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "close_time": int(row[6]),
            }
            for row in data
        ]

    def _load_candles_from_csv(self, dataset_id: str) -> list[dict]:
        path = self.import_root / f"{dataset_id}.csv"
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSV dataset not found.")
        rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
        candles = []
        for row in rows:
            timestamp = self._parse_timestamp(row["timestamp"])
            candles.append(
                {
                    "open_time": int(timestamp.timestamp() * 1000),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                    "close_time": int(timestamp.timestamp() * 1000),
                }
            )
        return candles

    def _snapshot_from_candles(self, symbol: str, candles: list[dict]) -> dict:
        close = Decimal(str(candles[-1]["close"]))
        best_bid = close * Decimal("0.999")
        best_ask = close * Decimal("1.001")
        bundle = {
            "symbol": symbol,
            "rules": {},
            "orderbook": {
                "bids": [{"price": _fmt_decimal(best_bid), "quantity": "10"}],
                "asks": [{"price": _fmt_decimal(best_ask), "quantity": "8"}],
                "best_bid": _fmt_decimal(best_bid),
                "best_ask": _fmt_decimal(best_ask),
                "spread_pct": _fmt_decimal(((best_ask - best_bid) / close) * Decimal("100")),
            },
            "recent_trades": [],
            "candles": candles,
            "source": "BINANCE_BACKTEST",
            "tabdeal_price": close,
            "analysis_close": close,
            "source_price_diff_pct": Decimal("0"),
        }
        return build_market_snapshot(bundle)

    def _analyze_strategy(self, strategy_name: str, config_json: dict, snapshot: dict, open_positions: list[dict]) -> dict:
        strategy_upper = strategy_name.upper()
        if strategy_upper == "AI_TECHNICAL_GUARD":
            guard = self.technical_guard.evaluate(snapshot, "BUY")
            if guard["allowed"]:
                return {"action": "BUY", "confidence": 68, "reason": "Technical guard passed in backtest mode.", "take_profit_pct": 2, "stop_loss_pct": 1}
            return {"action": "HOLD", "confidence": 45, "reason": "Technical guard blocked backtest entry.", "take_profit_pct": None, "stop_loss_pct": None}
        return self.strategy_engine.analyze(strategy_upper, config_json, snapshot, {}, open_positions)

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        if value.isdigit():
            return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)


backtest_engine = BacktestEngine()
