from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

from core.models import MarketIndicator, MarketSnapshot
from data.errors import RateLimitedError
from data.provider import MarketDataProvider


class FinnhubProvider(MarketDataProvider):
    name = "finnhub"

    def __init__(
        self,
        api_key: Optional[str],
        timeout: int = 15,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if not api_key:
            raise ValueError("FINNHUB_API_KEY is required for FinnhubProvider")
        self.api_key = api_key
        self.timeout = timeout
        self._transport = transport

    async def _get_json(self, path: str, params: dict) -> dict:
        url = f"https://finnhub.io/api/v1{path}"
        params = {**params, "token": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            response = await client.get(url, params=params)
            if response.status_code == 429 or response.status_code >= 500:
                raise RateLimitedError(f"Finnhub temporary error: {response.status_code}")
            response.raise_for_status()
            return response.json()

    async def get_snapshot(self, symbols: List[str]) -> MarketSnapshot:
        indicators: Dict[str, MarketIndicator] = {}
        for symbol in symbols:
            data = await self._get_json("/quote", {"symbol": symbol.upper()})
            price = data.get("c")
            if price is None:
                raise ValueError(f"Missing price for {symbol}")
            indicators[symbol] = MarketIndicator(price=round(float(price), 2), volume=None)
        return MarketSnapshot(as_of=datetime.utcnow(), indicators=indicators, provider=self.name)

    async def get_history(self, symbol: str, days: int = 30) -> list[dict]:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        data = await self._get_json(
            "/stock/candle",
            {
                "symbol": symbol.upper(),
                "resolution": "D",
                "from": int(start.timestamp()),
                "to": int(end.timestamp()),
            },
        )
        if data.get("s") != "ok":
            raise ValueError(f"Finnhub candle error for {symbol}: {data.get('s')}")
        history: list[dict] = []
        for idx, ts in enumerate(data.get("t", [])):
            history.append(
                {
                    "date": datetime.utcfromtimestamp(ts).date().isoformat(),
                    "open": float(data["o"][idx]),
                    "high": float(data["h"][idx]),
                    "low": float(data["l"][idx]),
                    "close": float(data["c"][idx]),
                    "volume": int(data["v"][idx]),
                    "symbol": symbol.upper(),
                }
            )
        return history
