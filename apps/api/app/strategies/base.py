from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyDecision:
    action: str
    confidence: int
    reason: str
    entry_price: float | None
    take_profit_pct: float | None
    stop_loss_pct: float | None
    metadata: dict[str, Any] = field(default_factory=dict)


class StrategyBase:
    name = "BASE"

    def analyze(self, config: dict, market_snapshot: dict, account_snapshot: dict, open_positions: list[dict]) -> StrategyDecision:
        raise NotImplementedError
