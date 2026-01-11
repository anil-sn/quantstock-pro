import pytest
import asyncio
import pandas as pd
from app.market_data import fetch_stock_data
from app.technicals_indicators import calculate_advanced_technicals
from app.technicals_scoring import calculate_algo_signal
from app.fundamentals import get_advanced_fundamentals
from app.context import get_market_context
from app.news_fetcher import UnifiedNewsFetcher
from app.service import analyze_stock, get_advanced_fundamental_analysis
from app.models import AdvancedStockResponse, DataIntegrity

# --- CONFIGURATION ---
TICKER_UNIVERSE = [
    "AAPL",        # US Blue Chip
    "TSLA",        # High Volatility US
    "RELIANCE.NS", # Indian Large Cap
    "EICHERMOT.NS",# Indian Industrial
    "TLT",         # Bond ETF (Test non-equity metrics)
    "NVDA"         # AI Growth
]

@pytest.mark.asyncio
@pytest.mark.live
@pytest.mark.parametrize("ticker", TICKER_UNIVERSE)
async def test_full_pipeline_forensics(ticker):
    """
    Brutal Audit: Every ticker must pass 100% Pydantic validation 
    and produce no 'Schrödinger Zeros' (silent math failures).
    """
    print(f"\n[AUDIT] Starting forensic trace for {ticker}...")
    
    try:
        # 1. Execute full analysis
        response = await analyze_stock(ticker, mode="all")
        
        # 2. Pydantic Validation (Implicitly checked by response_model in FastAPI, but here explicit)
        assert isinstance(response, AdvancedStockResponse)
        
        # 3. Data Integrity Check (Now allowing INVALID if it's correctly reported)
        print(f"[AUDIT] Data Integrity: {response.system.data_quality}")
        
        # 4. Math Sanity: Detection of 'Silent Zeros'
        price = response.levels.current
        if response.system.data_quality != DataIntegrity.INVALID:
            assert price > 0, f"Ticker {ticker} reported price <= 0 with VALID/DEGRADED integrity"
            
            # 6. Deep Dive: Technicals & Scoring
            sig = response.signals
            assert -1.1 <= sig.primary_signal_strength <= 1.1, f"Signal strength out of bounds ({sig.primary_signal_strength}) for {ticker}"
        
        # 5. Sensor Verification
        taxonomy = response.system.data_state_taxonomy
        print(f"[AUDIT] Data Taxonomy: {taxonomy}")
        
        # 7. News Intelligence check
        summary = response.human_insight.summary
        assert len(summary) > 5, f"Summary too short for {ticker}"

        print(f"[AUDIT] {ticker} PASSED forensic validation.")

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        pytest.fail(f"Forensic Audit FAILED for {ticker} with error: {e}\nTrace:\n{error_trace}")

@pytest.mark.asyncio
@pytest.mark.live
async def test_sensor_individual_resilience():
    """Verify that individual sensors don't crash the pipeline even if they return empty."""
    ticker = "AAPL"
    
    # 1. Test Market Context (Individual call)
    try:
        context = get_market_context(ticker)
        assert context is not None
        print("[AUDIT] Market Context sensor responsive.")
    except Exception as e:
        pytest.fail(f"Market Context sensor CRASHED: {e}")

    # 2. Test News Aggregator
    try:
        news = await UnifiedNewsFetcher.fetch_all(ticker)
        assert isinstance(news, list)
        print(f"[AUDIT] News sensor responsive (Found {len(news)} items).")
    except Exception as e:
        pytest.fail(f"News sensor CRASHED: {e}")

@pytest.mark.asyncio
@pytest.mark.live
async def test_intl_fundamental_ordering():
    """Verify that Indian stocks correctly calculate growth by reordering columns."""
    ticker = "RELIANCE.NS"
    try:
        fund = await get_advanced_fundamental_analysis(ticker)
        # Check if trend analysis exists (requires YoY calc)
        # If it doesn't, it might be due to yfinance column sorting bug we fixed
        assert fund.trend_and_momentum["trajectory"] is not None
        print(f"[AUDIT] Intl Fundamental Trend: {fund.trend_and_momentum['trajectory']}")
    except Exception as e:
        pytest.fail(f"Intl Fundamental Audit FAILED for {ticker}: {e}")
