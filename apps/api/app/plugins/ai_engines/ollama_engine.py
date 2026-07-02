from __future__ import annotations

from typing import Any

import httpx

from app.plugins.ai_engines.base import BaseAIEngine


class OllamaEngine(BaseAIEngine):
    name = "OLLAMA"
    description = "Local Ollama HTTP adapter"
    config_schema = {"base_url": "string", "model": "string"}

    async def healthcheck(self, config: dict[str, Any]) -> dict[str, Any]:
        base_url = config["base_url"].rstrip("/")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
        return {"ok": True, "models": [item.get("name") for item in data.get("models", [])]}

    async def analyze(self, payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        base_url = config["base_url"].rstrip("/")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": config["model"],
                    "prompt": payload["prompt"],
                    "format": "json",
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
        if "response" not in data:
            raise ValueError("Ollama response field missing.")
        import json

        return json.loads(data["response"])
