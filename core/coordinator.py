from __future__ import annotations

import asyncio
import logging
from typing import Dict

from core.config import settings
from core.market_data import build_provider
from core.db import SessionLocal
from core.orchestrator import TradingOrchestrator
from data.provider import MarketDataProvider

logger = logging.getLogger("coordinator")


class Coordinator:
    def __init__(self, provider: MarketDataProvider | None = None):
        self.provider = provider or build_provider()
        self._tasks: Dict[int, asyncio.Task] = {}
        self._strategies: Dict[int, str] = {}

    async def start(self, user_id: int, strategy_text: str) -> None:
        self._strategies[user_id] = strategy_text
        if user_id in self._tasks and not self._tasks[user_id].done():
            return
        task = asyncio.create_task(self._run_loop(user_id))
        self._tasks[user_id] = task

    async def stop(self, user_id: int) -> None:
        task = self._tasks.get(user_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.pop(user_id, None)

    async def _run_loop(self, user_id: int) -> None:
        orchestrator = TradingOrchestrator(provider=self.provider)
        while True:
            try:
                async with SessionLocal() as session:
                    await orchestrator.run_cycle(session, user_id, self._strategies[user_id])
                    await session.commit()
            except Exception as exc:
                logger.exception("loop_error", exc_info=exc)
            await asyncio.sleep(settings.market_poll_seconds)
