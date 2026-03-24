class MarketDataError(Exception):
    pass


class RateLimitedError(MarketDataError):
    pass
