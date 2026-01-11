import pytest
import asyncio
from app.market_data import fetch_stock_data
from app.technicals_indicators import calculate_advanced_technicals
from app.technicals_scoring import calculate_algo_signal
from app.fundamentals_fetcher import fetch_raw_fundamentals
from app.fundamentals_analytics import FundamentalTrendEngine, IntrinsicValuationEngine
from app.news_fetcher import UnifiedNewsFetcher
from app.risk import RiskEngine, SetupState
from app.models import TradeAction

@pytest.mark.asyncio
@pytest.mark.live
async def test_step_1_raw_market_ingestion_aapl():
    """Verify L1: Raw data ingestion for a major US ticker."""
    ticker = "AAPL"
    data = await fetch_stock_data(ticker, interval="1d")
    
    assert data["info"] is not None
    assert not data["dataframe"].empty
    assert len(data["dataframe"]) >= 50
    assert "Close" in data["dataframe"].columns
    assert data["current_price"] > 0

@pytest.mark.asyncio
@pytest.mark.live
async def test_step_1_raw_market_ingestion_intl():
    """Verify L1: Raw data ingestion for an Indian ticker (EICHERMOT.NS)."""
    ticker = "EICHERMOT.NS"
    data = await fetch_stock_data(ticker, interval="1d")
    
    assert data["info"] is not None
    assert not data["dataframe"].empty
    assert data["current_price"] > 5000 # Eicher Motors is expensive

@pytest.mark.asyncio
@pytest.mark.live
async def test_step_2_technical_integrity_eichermot():
    """Verify L2: Mathematical integrity of CCI and other indicators for intl tickers."""
    ticker = "EICHERMOT.NS"
    data = await fetch_stock_data(ticker, interval="1d")
    tech = calculate_advanced_technicals(data["dataframe"])
    
    assert tech.rsi is not None
    assert tech.adx is not None
    # THE BIG ONE: Verify CCI fix
    assert tech.cci is not None, "CCI should not be None after robust fix!"
    assert -5000 < tech.cci < 5000, f"CCI value {tech.cci} seems like garbage"
    assert tech.ema_200 is not None

@pytest.mark.asyncio
@pytest.mark.live
async def test_step_3_fundamental_fallback_eichermot():
    """Verify L2: Fundamental statement fallback for international tickers."""
    ticker = "EICHERMOT.NS"
    # This calls our new fetch_raw_fundamentals with deep fallbacks
    data, info = fetch_raw_fundamentals(ticker)
    
    # Even if stock.info 404s, we should have pulled these from income_stmt/balance_sheet
    assert data.total_revenue is not None or data.market_cap is not None
    assert data.ticker == "EICHERMOT.NS"
    # Check if market cap was reconstructed
    assert data.market_cap > 0

@pytest.mark.asyncio
@pytest.mark.live
async def test_step_4_news_resilience():
    """Verify NewsAPI SSL resilience logic."""
    ticker = "TSLA"
    news = await UnifiedNewsFetcher.fetch_all(ticker)
    
    # We should get results even if one source (NewsAPI) has SSL issues
    assert isinstance(news, list)
    assert len(news) > 0
    assert news[0].title != ""

@pytest.mark.live
def test_step_5_valuation_math_nvda():
    """Verify DCF 3-Stage logic for high growth stocks."""
    # Mocking inputs for NVDA-like profile
    # NVDA FCF ~ 30B, Shares ~ 2.5B, Growth ~ 40%
    dcf = IntrinsicValuationEngine.calculate_dcf(
        fcf=30000000000,
        revenue_growth=0.40,
        shares=2500000000,
        fcf_margin=0.35
    )
    
    assert dcf["status"] in ["VALID", "TERMINAL_VALUE_DOMINANT_WARNING"]
    assert dcf["value"] > 0
    # Stage 2 (Fade) should contribute significantly to high growth DCF
    assert dcf["stage2_pv"] > 0

def test_step_6_risk_liquidity_cap():
    """Verify dynamic liquidity position sizing."""
    engine = RiskEngine()
    
    # Scenario: Low volume stock
    size_low_vol = engine.calculate_position_size(
        setup_state=SetupState.VALID,
        price=100.0,
        risk_per_share=2.0,
        avg_volume_20d=50000 # Very low volume
    )
    
    # Scenario: High volume stock
    size_high_vol = engine.calculate_position_size(
        setup_state=SetupState.VALID,
        price=100.0,
        risk_per_share=2.0,
        avg_volume_20d=5000000 # High volume
    )
    
    assert size_low_vol < size_high_vol, "Low volume should result in smaller position size"
    assert size_low_vol <= 1.0, "Low volume position should be capped heavily"
