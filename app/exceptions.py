class QuantStockError(Exception):
    """Base exception for all QuantStock errors."""
    pass

class SensorError(QuantStockError):
    """Raised when a data sensor fails."""
    pass

class TickerNotFoundError(SensorError):
    """Raised when a ticker is not found by the provider."""
    pass

class LiquidityHaltError(SensorError):
    """Raised when a stock is halted or has zero liquidity."""
    pass

class ProviderThrottledError(SensorError):
    """Raised when the data provider rate-limits the request."""
    pass

class DataIntegrityError(QuantStockError):
    """Raised when data is present but mathematically inconsistent."""
    pass
