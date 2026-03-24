from __future__ import annotations

from core.config import settings
from data.cache_provider import CachedMarketDataProvider
from data.finnhub import FinnhubProvider
from data.marketwatch import MarketWatchProvider
from data.mock_provider import MockMarketDataProvider
from data.provider import MarketDataProvider


def build_provider(name: str | None = None) -> MarketDataProvider:
    provider_name = (name or settings.market_data_provider).lower()
    if provider_name == "finnhub":
        provider: MarketDataProvider = FinnhubProvider(api_key=settings.finnhub_api_key)
    elif provider_name == "marketwatch":
        provider = MarketWatchProvider()
    elif provider_name == "mock":
        provider = MockMarketDataProvider()
    else:
        raise ValueError(f"Unknown market data provider: {provider_name}")
    return CachedMarketDataProvider(provider)
