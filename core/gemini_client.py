from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from core.config import settings


class GeminiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

    async def generate(self, prompt: str) -> str:
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                params={"key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return self._extract_text(data)

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        text = await self.generate(prompt)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned invalid JSON: {text}") from exc

    @staticmethod
    def _extract_text(payload: Dict[str, Any]) -> str:
        candidates = payload.get("candidates") or []
        if not candidates:
            raise ValueError("No candidates returned from Gemini")
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise ValueError("No content parts in Gemini response")
        return parts[0].get("text", "")
