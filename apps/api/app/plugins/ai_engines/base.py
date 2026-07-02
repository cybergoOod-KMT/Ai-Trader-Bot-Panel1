from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAIEngine(ABC):
    name = "BASE"
    description = "Base AI engine"
    config_schema: dict[str, Any] = {}

    @abstractmethod
    async def healthcheck(self, config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def analyze(self, payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
