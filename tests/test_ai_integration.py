import pytest
from app.ai import interpret_advanced, _create_deterministic_analysis
from app.service import analyze_stock
from app.models import (
    TechnicalStockResponse, StockOverview, TradeAction, ScoreDetail, 
    MultiHorizonSetups, TradeSetup, SetupState, PipelineState, 
    PipelineStageState, DecisionState, DataIntegrity
)

@pytest.mark.asyncio
async def test_ai_deterministic_bypass_on_reject():
    """Verify that REJECT state triggers deterministic bypass without LLM call."""
    # 1. Setup a rejected response
    overview = StockOverview(
        action=TradeAction.REJECT, current_price=100.0, 
        confidence=ScoreDetail(value=0, min_value=0, max_value=100, label="None", legend=""),
        summary="Violates framework rules"
    )
    
    tech_resp = TechnicalStockResponse(
        overview=overview, requested_ticker="AAPL", ticker="AAPL",
        current_price=100.0,
        trade_setup=TradeSetup(action=TradeAction.REJECT, confidence=overview.confidence, setup_state=SetupState.INVALID),
        decision_state=DecisionState.REJECT,
        data_confidence=0.0,
        data_integrity=DataIntegrity.INVALID
    )
    
    # 2. Call interpret_advanced (it should return deterministic result immediately)
    result = await interpret_advanced(tech_resp)
    
    assert result is not None
    assert "AUTOMATED REJECTION" in result.executive_summary
    assert result.intraday.action == TradeAction.REJECT

@pytest.mark.asyncio
async def test_ai_deterministic_bypass_on_low_confidence():
    """Verify that low confidence WAIT state triggers deterministic bypass."""
    overview = StockOverview(
        action=TradeAction.WAIT, current_price=100.0, 
        confidence=ScoreDetail(value=10, min_value=0, max_value=100, label="Low", legend=""),
        summary="Insufficient signals"
    )
    
    tech_resp = TechnicalStockResponse(
        overview=overview, requested_ticker="AAPL", ticker="AAPL",
        current_price=100.0,
        trade_setup=TradeSetup(action=TradeAction.WAIT, confidence=overview.confidence, setup_state=SetupState.VALID),
        decision_state=DecisionState.WAIT,
        data_confidence=10.0, # Below 30 threshold
        data_integrity=DataIntegrity.DEGRADED
    )
    
    result = await interpret_advanced(tech_resp)
    
    assert result is not None
    assert "AUTOMATED REJECTION" in result.executive_summary
    assert result.intraday.action == TradeAction.WAIT

def test_deterministic_analysis_construction():
    """Verify the static object creation for rejections."""
    overview = StockOverview(
        action=TradeAction.REJECT, current_price=150.0, 
        confidence=ScoreDetail(value=0, min_value=0, max_value=100, label="None", legend=""),
        summary="Insider selling detected"
    )
    tech_resp = TechnicalStockResponse(
        overview=overview, requested_ticker="AAPL", ticker="AAPL",
        current_price=150.0,
        trade_setup=TradeSetup(action=TradeAction.REJECT, confidence=overview.confidence),
        decision_state=DecisionState.REJECT
    )
    
    result = _create_deterministic_analysis(tech_resp, None)
    assert "Insider selling" in result.executive_summary
    assert result.intraday.action == TradeAction.REJECT

@pytest.mark.asyncio
async def test_prompt_construction_contains_data_blocks():
    """Verify that the constructed prompt contains all necessary XML blocks."""
    from unittest.mock import patch, AsyncMock
    
    overview = StockOverview(
        action=TradeAction.BUY, current_price=100.0, 
        confidence=ScoreDetail(value=80, min_value=0, max_value=100, label="High", legend=""),
        summary="Audit pass"
    )
    tech_resp = TechnicalStockResponse(
        overview=overview, requested_ticker="AAPL", ticker="AAPL",
        current_price=100.0,
        trade_setup=TradeSetup(action=TradeAction.BUY, confidence=overview.confidence),
        decision_state=DecisionState.ACCEPT,
        data_confidence=85.0
    )
    
    # We mock _interpret_cached to capture the prompt passed to it
    with patch("app.ai._interpret_cached", new_callable=AsyncMock) as mock_interpret:
        await interpret_advanced(tech_resp)
        
        # Get the first argument of the first call (which is the prompt)
        # arg 0: ticker, arg 1: prompt
        call_args = mock_interpret.call_args[0]
        prompt = call_args[1]
        
        assert "<MARKET_DATA>" in prompt
        assert "</MARKET_DATA>" in prompt
        assert "Technical Horizons & Signals:" in prompt
        assert "Fundamental Assessment:" in prompt
        assert "Smart Money Context:" in prompt
        assert "Latest News Headlines:" in prompt
        assert "AAPL" in prompt

@pytest.mark.asyncio
@pytest.mark.live
async def test_live_ai_synthesis_forced():
    """
    ULTIMATE TEST: Force a real Gemini AI call for a live ticker
    and verify that it bypasses the fast path and returns a full synthesis.
    """
    ticker = "EICHERMOT.NS"
    print(f"\n[AI_AUDIT] Requesting FORCED AI synthesis for {ticker}...")
    
    # force_ai=True ignores signal strength/latency thresholds
    response = await analyze_stock(ticker, mode="all", force_ai=True)
    
    assert response.system.engine_logic == "HYBRID", "System should have used HYBRID (AI) engine but used DETERMINISTIC"
    assert response.ai_analysis is not None, "AI analysis block is missing"
    assert len(response.human_insight.summary) > 50, "AI summary is too short, likely didn't run full synthesis"
    
    # Verify that the summary isn't the deterministic 'Audit complete' string
    assert "Audit complete" not in response.human_insight.summary
    print(f"[AI_AUDIT] Live AI Response Received. Summary Preview: {response.human_insight.summary[:100]}...")
