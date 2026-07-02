from __future__ import annotations

from fastapi import HTTPException, status

from app.plugins.ai_engines.base import BaseAIEngine
from app.plugins.ai_engines.ollama_engine import OllamaEngine
from app.plugins.ai_engines.openai_engine import OpenAIEngine


class AIEngineRegistry:
    def __init__(self) -> None:
        self._engines: dict[str, BaseAIEngine] = {
            OpenAIEngine.name: OpenAIEngine(),
            OllamaEngine.name: OllamaEngine(),
        }

    def list_engines(self) -> list[dict]:
        return [
            {"name": engine.name, "description": engine.description, "config_schema": engine.config_schema}
            for engine in self._engines.values()
        ]

    def get(self, name: str) -> BaseAIEngine:
        engine = self._engines.get(name.upper())
        if not engine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI engine not found.")
        return engine


ai_engine_registry = AIEngineRegistry()
