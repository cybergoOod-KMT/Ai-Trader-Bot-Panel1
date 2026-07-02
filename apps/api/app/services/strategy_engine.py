from fastapi import HTTPException, status

from app.plugins.strategies.registry import strategy_registry


class StrategyEngine:
    def list_strategies(self) -> list[dict]:
        return strategy_registry.list()

    def get_strategy(self, name: str):
        try:
            return strategy_registry.get(name)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found.") from exc

    def analyze(self, name: str, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> dict:
        strategy = self.get_strategy(name)
        decision = strategy.analyze(config, market_snapshot, account_snapshot, open_positions)
        return {
            "action": decision.action,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "entry_price": decision.entry_price,
            "take_profit_pct": decision.take_profit_pct,
            "stop_loss_pct": decision.stop_loss_pct,
            "metadata": decision.metadata,
        }
