from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.plugins.ai_engines.base import BaseAIEngine


class OpenAIEngine(BaseAIEngine):
    name = "OPENAI"
    description = "OpenAI Responses API engine"
    config_schema = {"api_key": "string", "model": "string"}
    decision_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["BUY_NOW", "BUY_AFTER_BREAKOUT", "WAIT_PULLBACK", "SELL", "HOLD"]},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "reason": {"type": "string"},
            "entry_note": {"type": "string"},
            "entry_price": {"type": ["number", "null"]},
            "breakout_price": {"type": ["number", "null"]},
            "pullback_price": {"type": ["number", "null"]},
            "take_profit_pct": {"type": "number"},
            "stop_loss_pct": {"type": "number"},
            "risk_warning": {"type": "string"},
            "technical_summary": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "trend": {"type": "string", "enum": ["bullish", "bearish", "range", "unclear"]},
                    "momentum": {"type": "string", "enum": ["strong", "weak", "neutral"]},
                    "volume": {"type": "string", "enum": ["high", "normal", "low"]},
                    "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["trend", "momentum", "volume", "risk_level"],
            },
        },
        "required": [
            "action",
            "confidence",
            "reason",
            "entry_note",
            "entry_price",
            "breakout_price",
            "pullback_price",
            "take_profit_pct",
            "stop_loss_pct",
            "risk_warning",
            "technical_summary",
        ],
    }

    def _build_client(self, api_key: str) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=api_key, base_url=get_settings().openai_api_base_url)

    async def healthcheck(self, config: dict[str, Any]) -> dict[str, Any]:
        client = self._build_client(config["api_key"])
        response = await client.responses.create(model=config["model"], input="Reply with exactly OK", max_output_tokens=16)
        return {"ok": True, "model": response.model, "response_id": response.id}

    async def analyze(self, payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        client = self._build_client(config["api_key"])
        response = await client.responses.create(
            model=config["model"],
            input=payload["prompt"],
            max_output_tokens=900,
            text={"format": {"type": "json_schema", "name": "ai_decision", "schema": self.decision_schema, "strict": True}},
        )
        content = (getattr(response, "output_text", "") or "").strip()
        return json.loads(content)
