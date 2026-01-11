import pytest
from app.providers.yahoo import YahooProvider
from app.exceptions import TickerNotFoundError, SensorError

@pytest.mark.asyncio
async def test_yahoo_provider_fetch_history_valid():
    """Verify history fetch for a valid ticker."""
    provider = YahooProvider()
    df = await provider.fetch_price_history("AAPL", interval="1d", period="1mo")
    assert not df.empty
    assert "Close" in df.columns

@pytest.mark.asyncio
async def test_yahoo_provider_fetch_history_invalid():
    """Verify exception handling for an invalid ticker."""
    provider = YahooProvider()
    with pytest.raises(TickerNotFoundError):
        await provider.fetch_price_history("INVALID_TICKER_12345", interval="1d", period="1mo")

@pytest.mark.asyncio
async def test_yahoo_provider_fetch_info_valid():
    """Verify info fetch for a valid ticker."""
    provider = YahooProvider()
    info = await provider.fetch_ticker_info("AAPL")
    assert isinstance(info, dict)
    assert info.get("symbol") == "AAPL" or info.get("longName") is not None

@pytest.mark.asyncio
async def test_yahoo_provider_reconstruction_fallback():
    """
    Verify fallback logic for tickers where .info fails.
    RELIANCE.NS is a stable intl ticker to verify reconstruction if needed.
    """
    provider = YahooProvider()
    info = await provider.fetch_ticker_info("RELIANCE.NS")
    assert isinstance(info, dict)
    assert "RELIANCE" in str(info.get("longName")).upper() or "RELIANCE" in str(info.get("shortName")).upper()
