import httpx
import pytest

from data.cache_provider import CachedMarketDataProvider
from data.finnhub import FinnhubProvider


@pytest.mark.asyncio
async def test_finnhub_snapshot_parsing():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/quote"):
            return httpx.Response(200, json={"c": 123.45})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    provider = FinnhubProvider(api_key="test", transport=transport)
    snapshot = await provider.get_snapshot(["AAPL"])
    assert snapshot.indicators["AAPL"].price == 123.45
    assert snapshot.provider == "finnhub"


@pytest.mark.asyncio
async def test_finnhub_rate_limit_uses_cache():
    call_count = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/quote"):
            call_count["count"] += 1
            if call_count["count"] == 1:
                return httpx.Response(200, json={"c": 50.0})
            return httpx.Response(429, json={"error": "rate limit"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    provider = FinnhubProvider(api_key="test", transport=transport)
    cached = CachedMarketDataProvider(provider, ttl_seconds=0)
    first = await cached.get_snapshot(["AAPL"])
    second = await cached.get_snapshot(["AAPL"])
    assert second.indicators["AAPL"].price == 50.0
    assert second.as_of == first.as_of


@pytest.mark.asyncio
async def test_finnhub_history_parsing():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/stock/candle"):
            return httpx.Response(
                200,
                json={
                    "s": "ok",
                    "t": [1700000000, 1700086400],
                    "o": [100, 101],
                    "h": [105, 106],
                    "l": [95, 96],
                    "c": [102, 103],
                    "v": [1000, 1200],
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    provider = FinnhubProvider(api_key="test", transport=transport)
    history = await provider.get_history("AAPL", days=2)
    assert len(history) == 2
    assert history[0]["open"] == 100.0
    assert history[1]["close"] == 103.0
