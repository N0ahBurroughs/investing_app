from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from core.models import MarketSnapshot


class MarketDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def get_snapshot(self, symbols: List[str]) -> MarketSnapshot:
        raise NotImplementedError

    @abstractmethod
    async def get_history(self, symbol: str, days: int = 30) -> list[dict]:
        raise NotImplementedError
