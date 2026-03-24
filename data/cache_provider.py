from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from core.models import MarketSnapshot
from data.errors import RateLimitedError
from data.provider import MarketDataProvider


class CachedMarketDataProvider(MarketDataProvider):
    name = "cached"

    def __init__(
        self,
        provider: MarketDataProvider,
        ttl_seconds: int = 30,
        base_backoff_seconds: int = 5,
        max_backoff_seconds: int = 300,
    ):
        self.provider = provider
        self.ttl = timedelta(seconds=ttl_seconds)
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self._cache: Dict[Tuple[str, ...], MarketSnapshot] = {}
        self._cache_time: Dict[Tuple[str, ...], datetime] = {}
        self._backoff_seconds: int | None = None
        self._backoff_until: datetime | None = None

    async def get_snapshot(self, symbols: List[str]) -> MarketSnapshot:
        key = tuple(sorted(symbols))
        now = datetime.utcnow()
        cached = self._cache.get(key)
        cached_time = self._cache_time.get(key)

        if cached and cached_time and now - cached_time <= self.ttl:
            return cached

        if self._backoff_until and now < self._backoff_until and cached:
            return cached

        try:
            snapshot = await self.provider.get_snapshot(symbols)
            self._cache[key] = snapshot
            self._cache_time[key] = now
            self._backoff_seconds = None
            self._backoff_until = None
            return snapshot
        except RateLimitedError:
            self._apply_backoff(now)
            if cached:
                return cached
            raise
        except Exception:
            if cached:
                return cached
            raise

    async def get_history(self, symbol: str, days: int = 30) -> list[dict]:
        return await self.provider.get_history(symbol, days=days)

    def _apply_backoff(self, now: datetime) -> None:
        if self._backoff_seconds is None:
            self._backoff_seconds = self.base_backoff_seconds
        else:
            self._backoff_seconds = min(self._backoff_seconds * 2, self.max_backoff_seconds)
        self._backoff_until = now + timedelta(seconds=self._backoff_seconds)
