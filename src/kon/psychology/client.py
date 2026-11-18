"""
Mini Modex Psychology API Client

Connects to the mini-modex TypeScript psychology engine running as a REST API.
Default: http://localhost:18083
"""

from __future__ import annotations

import json
import os
from typing import Any

import aiohttp


class PsychologyClientError(Exception):
    """Error communicating with mini-modex API."""


class PsychologyClient:
    """HTTP client for mini-modex psychology API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url or os.environ.get(
            "PSYCHOLOGY_API_URL", "http://localhost:18083"
        )
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def health_check(self) -> bool:
        """Check if mini-modex API is reachable."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/v1/models") as resp:
                return resp.status == 200
        except Exception:
            return False

    async def detect_emotion(self, message: str) -> dict[str, Any]:
        """Detect emotion from user message."""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/v1/psychology/detect",
            json={"message": message},
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise PsychologyClientError(
                    f"Emotion detection failed: {resp.status} {error_text}"
                )
            return await resp.json()

    async def choose_strategy(
        self,
        message: str,
        emotion: str,
        conversation_history: list[str] | None = None,
    ) -> dict[str, Any]:
        """Choose therapeutic strategy based on emotion and context."""
        session = await self._get_session()
        payload: dict[str, Any] = {
            "message": message,
            "emotion": emotion,
        }
        if conversation_history:
            payload["conversation_history"] = conversation_history

        async with session.post(
            f"{self.base_url}/v1/psychology/strategy",
            json=payload,
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise PsychologyClientError(
                    f"Strategy selection failed: {resp.status} {error_text}"
                )
            return await resp.json()

    async def get_state(self) -> dict[str, Any]:
        """Get current psychology state."""
        session = await self._get_session()
        async with session.get(f"{self.base_url}/v1/psychology/state") as resp:
            if resp.status != 200:
                raise PsychologyClientError(
                    f"State fetch failed: {resp.status}"
                )
            return await resp.json()

    async def update_user_model(
        self,
        message: str,
        emotion: str,
        intensity: float,
    ) -> dict[str, Any]:
        """Update user model with conversation data."""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/v1/psychology/user-model",
            json={
                "message": message,
                "emotion": emotion,
                "intensity": intensity,
            },
        ) as resp:
            if resp.status != 200:
                raise PsychologyClientError(
                    f"User model update failed: {resp.status}"
                )
            return await resp.json()

    async def record_pattern(
        self,
        pattern_type: str,
        effectiveness: float,
    ) -> dict[str, Any]:
        """Record a conversation pattern usage."""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/v1/psychology/pattern",
            json={
                "pattern_type": pattern_type,
                "effectiveness": effectiveness,
            },
        ) as resp:
            if resp.status != 200:
                raise PsychologyClientError(
                    f"Pattern recording failed: {resp.status}"
                )
            return await resp.json()

    async def get_patterns_summary(self) -> str:
        """Get conversation patterns summary."""
        session = await self._get_session()
        async with session.get(f"{self.base_url}/v1/psychology/patterns") as resp:
            if resp.status != 200:
                return "No patterns recorded yet."
            data = await resp.json()
            return data.get("summary", "No patterns recorded yet.")

    async def get_goals_summary(self) -> str:
        """Get therapeutic goals summary."""
        session = await self._get_session()
        async with session.get(f"{self.base_url}/v1/psychology/goals") as resp:
            if resp.status != 200:
                return "No therapeutic goals set."
            data = await resp.json()
            return data.get("summary", "No therapeutic goals set.")
