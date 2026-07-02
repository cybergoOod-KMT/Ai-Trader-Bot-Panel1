from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseExchangeConnector(ABC):
    name = "BASE"
    capabilities: list[str] = []

    @abstractmethod
    async def healthcheck(self) -> dict[str, Any]:
        raise NotImplementedError
