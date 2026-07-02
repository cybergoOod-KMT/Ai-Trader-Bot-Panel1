from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class OpenAIConnectionError(Exception):
    pass


class OpenAIConnectionClient:
    def __init__(self, api_key: str, model: str) -> None:
        settings = get_settings()
        self.api_key = api_key
        self.model = model
        self.endpoint = settings.openai_url

    async def test_connection(self) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "input": "Reply with exactly: OK",
            "max_output_tokens": 16,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise OpenAIConnectionError(self._extract_error_message(exc.response)) from exc
        except httpx.TimeoutException as exc:
            raise OpenAIConnectionError("OpenAI request timed out.") from exc
        except httpx.HTTPError as exc:
            raise OpenAIConnectionError("OpenAI service is unavailable.") from exc

        data = response.json()
        return {
            "id": data.get("id"),
            "model": data.get("model", self.model),
            "output_text": self._extract_output_text(data),
        }

    def _extract_error_message(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"OpenAI request failed with status {response.status_code}."

        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        return f"OpenAI request failed with status {response.status_code}."

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        segments: list[str] = []
        output = payload.get("output")
        if not isinstance(output, list):
            return ""

        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for chunk in content:
                if not isinstance(chunk, dict):
                    continue
                text_value = chunk.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    segments.append(text_value.strip())
        return "\n".join(segments).strip()
