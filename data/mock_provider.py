from __future__ import annotations

from datetime import datetime, timedelta
from random import Random
from typing import Dict, List

from core.models import MarketIndicator, MarketSnapshot
from data.provider import MarketDataProvider


class MockMarketDataProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, seed: int = 42):
        self.random = Random(seed)

    async def get_snapshot(self, symbols: List[str]) -> MarketSnapshot:
        indicators: Dict[str, MarketIndicator] = {}
        for symbol in symbols:
            base = self.random.uniform(80, 220)
            sma = base + self.random.uniform(-5, 5)
            rsi = self.random.uniform(35, 75)
            vol = self.random.uniform(0.1, 0.6)
            indicators[symbol] = MarketIndicator(
                price=round(base, 2),
                sma_20=round(sma, 2),
                rsi_14=round(rsi, 2),
                volatility_20=round(vol, 4),
                volume=int(self.random.uniform(1e6, 5e6)),
            )
        return MarketSnapshot(as_of=datetime.utcnow(), indicators=indicators, provider=self.name)

    async def get_history(self, symbol: str, days: int = 30) -> list[dict]:
        series = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i)
            base = self.random.uniform(80, 220)
            series.append({"date": date.date().isoformat(), "close": round(base, 2), "volume": int(self.random.uniform(1e6, 5e6)), "symbol": symbol})
        return series
