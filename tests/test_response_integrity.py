import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models_v2 import AnalysisResponse, HealthResponse
from app.models import DecisionState, TradeAction, SetupState, DataIntegrity

client = TestClient(app)

@pytest.mark.live
@pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "EICHERMOT.NS"])
def test_exhaustive_response_validation(ticker):
    """
    BRUTAL VALIDATION: Every single field in the AnalysisResponse is audited.
    """
    response = client.get(f"/api/v2/analysis/{ticker}")
    assert response.status_code == 200
    
    # 1. Schema Validation
    try:
        data = AnalysisResponse.model_validate(response.json())
    except Exception as e:
        pytest.fail(f"SCHEMA BREACH for {ticker}: {e}")

    # 2. Meta Info (MetaInfo)
    assert data.meta.ticker == ticker.upper()
    assert data.meta.version == "2.0.0"
    assert len(data.meta.analysis_id) > 5
    assert data.meta.timestamp is not None

    # 3. Execution Block (ExecutionBlock)
    # Note: data.execution is Dict[str, Any] in AnalysisResponse model
    exec_b = data.execution
    assert exec_b["action"] in [a.value for a in TradeAction]
    assert isinstance(exec_b["authorized"], bool)
    assert exec_b["urgency"] in ["LOW", "MEDIUM", "HIGH", "IMMEDIATE"]
    
    rl = exec_b["risk_limits"]
    assert 0 <= rl["max_position_pct"] <= 25.0
    assert 0 <= rl["max_capital_risk_pct"] <= 5.0
    assert rl["daily_loss_limit_pct"] == 3.0
    
    if exec_b["action"] == "REJECT":
        assert exec_b["authorized"] is False
        # If REJECT, there must be a reason in the summary or a veto
        summary = data.human_insight.summary.lower()
        has_vetoes = len(exec_b.get("vetoes", [])) > 0
        has_reject_keywords = any(kw in summary for kw in ["reject", "violation", "veto", "blocked", "locked", "insufficient"])
        assert has_vetoes or has_reject_keywords or data.system.confidence < 40.0

    # 4. Signals Block (SignalsBlock)
    sig = data.signals
    assert -1.0 <= sig.primary_signal_strength <= 1.0
    assert 0.1 <= sig.required_strength <= 0.5
    assert sig.normalization_method == "Z-SCORE_CLAMPED"
    assert sig.expectancy_weighting == 0.25
    
    expected_components = {"trend", "momentum", "expectancy", "valuation"}
    assert set(sig.components.keys()) == expected_components
    for name, comp in sig.components.items():
        assert -2.0 <= comp.score <= 2.0
        assert 0.1 <= comp.weight <= 0.4
        assert len(comp.signal) > 0

    # 5. Levels Block (LevelsBlock)
    lvl = data.levels
    assert lvl.current > 0
    assert lvl.timestamp is not None
    for item in lvl.support + lvl.resistance:
        assert item.price > 0
        assert 0 <= item.strength <= 1.0
        assert len(item.type) > 0
        assert -100.0 <= item.distance_pct <= 100.0
    
    for zone in lvl.value_zones:
        assert zone.max >= zone.min
        assert 0 <= zone.attractiveness <= 1.0
        assert zone.type in ["SUPPORT_ZONE", "RECLAMATION_ZONE", "SUPPLY_ZONE"]

    # 6. Context Block (ContextBlock)
    ctx = data.context_v2
    assert ctx.regime in ["TRENDING", "RANGE_BOUND", "UNKNOWN"]
    assert 0 <= ctx.regime_confidence <= 1.0
    assert 0 <= ctx.trend_strength_adx <= 100.0
    assert 0 <= ctx.volatility_atr_pct <= 20.0
    assert 0 <= ctx.volume_ratio <= 10.0

    # 7. Human Insight Block (HumanInsightBlock)
    hi = data.human_insight
    assert len(hi.summary) > 10
    assert isinstance(hi.key_conflicts, list)
    assert "bullish" in hi.scenarios
    assert "bearish" in hi.scenarios
    assert hi.probability_basis == "HEURISTIC"

    # 8. System Block (SystemBlock)
    sys = data.system
    assert 0 <= sys.confidence <= 100.0
    assert sys.data_quality in [DataIntegrity.VALID, DataIntegrity.DEGRADED, DataIntegrity.INVALID]
    assert sys.latency_ms > 0
    assert sys.sla_threshold_ms == 5000.0
    assert isinstance(sys.fallback_used, bool)
    assert sys.engine_logic in ["HYBRID", "DETERMINISTIC"]
    assert "l0_l1_l2_sensors" in sys.layer_timings
    
    if sys.data_state_taxonomy.get("TECHNICALS") == "MISSING":
        assert sys.confidence == 0.0

    # 9. Technicals (TechnicalStockResponse)
    if data.technicals:
        t = data.technicals
        assert t.ticker == ticker.upper()
        assert t.current_price == lvl.current
        assert t.decision_state in [DecisionState.ACCEPT, DecisionState.WAIT, DecisionState.REJECT]
        if t.technicals:
            assert t.technicals.trend_structure is not None
        if t.algo_signal:
            assert t.algo_signal.overall_score.value is not None

    # 10. AI Insights (AIAnalysisResult)
    if data.ai_insights:
        ai = data.ai_insights
        assert len(ai.executive_summary) > 0
        for h_name in ["intraday", "swing", "positional", "longterm"]:
            h = getattr(ai, h_name)
            if h:
                assert h.confidence <= sys.confidence + 0.01
                assert h.action in [TradeAction.BUY, TradeAction.SELL, TradeAction.HOLD, TradeAction.WAIT, TradeAction.REJECT]
                if h.action in [TradeAction.BUY, TradeAction.SELL] and exec_b["authorized"]:
                    assert h.entry_price > 0
                    assert h.target_price > 0
                    assert h.stop_loss > 0
                for s in h.signals:
                    assert len(s.indicator) > 0
                    assert s.direction in ["Bullish", "Bearish", "Neutral"]
        
        if ai.market_sentiment:
            assert 0 <= ai.market_sentiment.score <= 100.0
            assert 0 <= ai.market_sentiment.fear_greed_index <= 100.0

    print(f"Verified {ticker} with BRUTAL depth.")

def test_v2_health_integrity():
    """Verify health endpoint field completeness."""
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    try:
        data = HealthResponse.model_validate(response.json())
    except Exception as e:
        pytest.fail(f"Health Response schema breach: {e}")
    
    assert data.status == "healthy"
    assert "market_data" in data.components
    assert "ai_engine" in data.components
    assert data.uptime_seconds > 0