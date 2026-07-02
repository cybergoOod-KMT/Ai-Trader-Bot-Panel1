from __future__ import annotations

from fastapi import HTTPException, status

from app.plugins.strategies.base import BaseStrategyPlugin
from app.plugins.strategies.builtins import (
    AiTechnicalGuardStrategy,
    DcaSimpleStrategy,
    EmaRsiVolumeStrategy,
    GridSimpleStrategy,
    MacdBreakoutStrategy,
    MeanReversionRsiStrategy,
    SupportResistanceBreakoutStrategy,
)


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, BaseStrategyPlugin] = {
            strategy.name: strategy
            for strategy in [
                EmaRsiVolumeStrategy(),
                MacdBreakoutStrategy(),
                SupportResistanceBreakoutStrategy(),
                MeanReversionRsiStrategy(),
                GridSimpleStrategy(),
                DcaSimpleStrategy(),
                AiTechnicalGuardStrategy(),
            ]
        }

    def list(self) -> list[dict]:
        return [
            {
                "name": item.name,
                "description": item.description,
                "config_schema": item.config_schema,
                "supports_backtest": item.supports_backtest,
            }
            for item in self._strategies.values()
        ]

    def get(self, name: str) -> BaseStrategyPlugin:
        strategy = self._strategies.get(name.upper())
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found.")
        return strategy


strategy_registry = StrategyRegistry()
