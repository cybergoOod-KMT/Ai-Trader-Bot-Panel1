from decimal import Decimal

from app.strategies.base import StrategyBase, StrategyDecision


class EmaRsiVolumeStrategy(StrategyBase):
    name = "EMA_RSI_VOLUME"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        ema9 = Decimal(market_snapshot["ema9"])
        ema21 = Decimal(market_snapshot["ema21"])
        ema50 = Decimal(market_snapshot["ema50"])
        price = Decimal(market_snapshot["analysis_close"])
        rsi = Decimal(market_snapshot["rsi14"])
        volume_ratio = Decimal(market_snapshot["volume_ratio"])
        if ema9 > ema21 and price > ema50 and Decimal("50") <= rsi <= Decimal("68") and volume_ratio >= Decimal("1.5"):
            return StrategyDecision("BUY", 76, "EMA/RSI/Volume alignment confirmed.", float(price), 3.0, 1.5, {})
        if rsi > Decimal("75") or price < ema21:
            return StrategyDecision("SELL", 68, "Momentum is overextended or price lost EMA21.", float(price), None, None, {})
        return StrategyDecision("HOLD", 52, "Conditions are not aligned yet.", None, None, None, {})


class MacdBreakoutStrategy(StrategyBase):
    name = "MACD_BREAKOUT"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        macd = Decimal(market_snapshot["macd"])
        signal = Decimal(market_snapshot["macd_signal"])
        hist = Decimal(market_snapshot["macd_histogram"])
        price = Decimal(market_snapshot["analysis_close"])
        resistance = Decimal(market_snapshot["resistance_20"])
        volume_ratio = Decimal(market_snapshot["volume_ratio"])
        if macd > signal and hist > 0 and price >= resistance * Decimal("0.999") and volume_ratio >= Decimal("1.5"):
            action = "BUY" if price >= resistance else "WATCH"
            return StrategyDecision(action, 74, "MACD breakout setup is active.", float(price), 3.0, 1.5, {"breakout_price": str(resistance)})
        return StrategyDecision("HOLD", 50, "MACD breakout setup is not confirmed.", None, None, None, {})


class SupportResistanceBreakoutStrategy(StrategyBase):
    name = "SUPPORT_RESISTANCE_BREAKOUT"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        price = Decimal(market_snapshot["analysis_close"])
        resistance = Decimal(market_snapshot["resistance_20"])
        volume_ratio = Decimal(market_snapshot["volume_ratio"])
        if price >= resistance * Decimal("1.001") and volume_ratio >= Decimal("1.5"):
            return StrategyDecision("BUY", 72, "Resistance breakout confirmed with volume.", float(price), 3.0, 1.5, {})
        if price >= resistance * Decimal("0.995"):
            return StrategyDecision("WATCH", 64, "Price is near resistance and needs breakout confirmation.", float(resistance), 3.0, 1.5, {"watch_type": "BREAKOUT"})
        return StrategyDecision("HOLD", 48, "No breakout setup yet.", None, None, None, {})


class MeanReversionRsiStrategy(StrategyBase):
    name = "MEAN_REVERSION_RSI"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        rsi = Decimal(market_snapshot["rsi14"])
        price = Decimal(market_snapshot["analysis_close"])
        support = Decimal(market_snapshot["support_20"])
        resistance = Decimal(market_snapshot["resistance_20"])
        near_support = abs((price - support) / price) <= Decimal("0.01")
        near_resistance = abs((price - resistance) / price) <= Decimal("0.01")
        if rsi < Decimal("30") and near_support:
            return StrategyDecision("BUY", 70, "Oversold RSI near support.", float(price), 2.5, 1.2, {})
        if rsi > Decimal("65") or near_resistance:
            return StrategyDecision("SELL", 65, "Mean reversion exit condition detected.", float(price), None, None, {})
        return StrategyDecision("HOLD", 49, "Mean reversion setup not ready.", None, None, None, {})


class GridSimpleStrategy(StrategyBase):
    name = "GRID_SIMPLE"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        return StrategyDecision(
            "WATCH",
            45,
            "Grid Simple is scaffolded for dry-run structure in Phase 3.",
            float(Decimal(market_snapshot["analysis_close"])),
            1.0,
            1.0,
            {"phase": "phase_3_scaffold"},
        )


class DcaSimpleStrategy(StrategyBase):
    name = "DCA_SIMPLE"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        price = Decimal(market_snapshot["analysis_close"])
        return StrategyDecision(
            "WATCH",
            52,
            "DCA Simple is waiting for next configured step drop.",
            float(price),
            2.0,
            1.5,
            {"max_steps": config.get("max_steps", 3), "step_drop_pct": config.get("step_drop_pct", 1.5)},
        )


class AiTechnicalGuardStrategy(StrategyBase):
    name = "AI_TECHNICAL_GUARD"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        return StrategyDecision("WATCH", 50, "Delegated to AI Engine + Technical Guard runtime.", None, None, None, {})


STRATEGY_REGISTRY = {
    item.name: item()
    for item in [
        EmaRsiVolumeStrategy,
        MacdBreakoutStrategy,
        SupportResistanceBreakoutStrategy,
        MeanReversionRsiStrategy,
        GridSimpleStrategy,
        DcaSimpleStrategy,
        AiTechnicalGuardStrategy,
    ]
}
