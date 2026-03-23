from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import MarketIndicator, MarketSnapshot
from data.provider import MarketDataProvider


class MarketWatchProvider(MarketDataProvider):
    name = "marketwatch"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _parse_price(self, html: str) -> float:
        soup = BeautifulSoup(html, "html.parser")
        price_tag = soup.find("bg-quote", {"class": "value"})
        if price_tag and price_tag.text:
            return float(price_tag.text.replace(",", ""))
        alt = soup.find("span", {"class": "value"})
        if alt and alt.text:
            return float(alt.text.replace(",", ""))
        raise ValueError("Unable to parse price from MarketWatch HTML")

    def _parse_volume(self, html: str) -> float | None:
        soup = BeautifulSoup(html, "html.parser")
        volume_tag = soup.find("bg-quote", {"field": "volume"})
        if volume_tag and volume_tag.text:
            text = volume_tag.text.replace(",", "").strip()
            if text.lower() in {"n/a", "--", ""}:
                return None
            return float(text)
        return None

    async def get_snapshot(self, symbols: List[str]) -> MarketSnapshot:
        indicators: Dict[str, MarketIndicator] = {}
        for symbol in symbols:
            url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
            html = await self._fetch(url)
            price = self._parse_price(html)
            volume = self._parse_volume(html)
            indicators[symbol] = MarketIndicator(price=round(price, 2), volume=volume)
        return MarketSnapshot(as_of=datetime.utcnow(), indicators=indicators, provider=self.name)

    async def get_history(self, symbol: str, days: int = 30) -> list[dict]:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        url = (
            f"https://www.marketwatch.com/investing/stock/{symbol.lower()}/download-data?"
            f"startDate={start_date.strftime('%m/%d/%Y')}&endDate={end_date.strftime('%m/%d/%Y')}"
        )
        csv_text = await self._fetch(url)
        lines = [line for line in csv_text.splitlines() if line and not line.lower().startswith("date")]
        history = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 6:
                continue
            history.append(
                {
                    "date": parts[0],
                    "open": float(parts[1]),
                    "high": float(parts[2]),
                    "low": float(parts[3]),
                    "close": float(parts[4]),
                    "volume": int(parts[5].replace(",", "")),
                    "symbol": symbol.upper(),
                }
            )
        return history
