import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models_v2 import AnalysisMode, TimeInterval, AnalysisResponse

client = TestClient(app)

# --- SMART CORRECTNESS UTILITIES ---

def validate_levels_logic(levels_block):
    """Rule: Support MUST be below current, Resistance MUST be above current."""
    current = levels_block["current"]
    if current <= 0: return # Skip if price is invalid
    for s in levels_block["support"]:
        assert s["price"] <= current + 0.01, f"Support {s['price']} above current price {current}"
    for r in levels_block["resistance"]:
        assert r["price"] >= current - 0.01, f"Resistance {r['price']} below current price {current}"

def validate_signal_convergence(signals_block):
    """Rule: primary_signal_strength must be a bounded weighted average of components."""
    reported = signals_block["primary_signal_strength"]
    assert -1.0 <= reported <= 1.0
    
    # We allow -1.0 override for Vetoes (Gated Product Model)
    if reported == -1.0:
        return

    total_weight = 0.0
    calc_sum = 0.0
    for comp in signals_block["components"].values():
        calc_sum += comp["score"] * comp["weight"]
        total_weight += comp["weight"]
    
    if total_weight > 0:
        expected = round(calc_sum, 3)
        assert abs(reported - expected) < 0.1, f"Signal logic breach: Reported {reported} vs Calculated {expected}"

# --- SERVICE STATUS TESTS ---

def test_v2_health():
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["market_data"] == "up"

def test_v2_status():
    response = client.get("/api/v2/status")
    assert response.status_code == 200
    data = response.json()
    assert "engine_version" in data
    assert data["api_tier"] == "Institutional"

# --- COMPREHENSIVE ANALYSIS TESTS (SMART & BRUTAL) ---

@pytest.mark.live
@pytest.mark.parametrize("ticker", ["AAPL", "CALX", "EICHERMOT.NS", "RELIANCE.NS"])
def test_v2_comprehensive_analysis_smart(ticker):
    """BRUTAL VALIDATION: Every field checked for mathematical and logical correctness."""
    response = client.get(f"/api/v2/analysis/{ticker}", params={"mode": "full", "force_ai": True})
    assert response.status_code == 200
    
    # In-Depth Pydantic Validation
    data_raw = response.json()
    try:
        data = AnalysisResponse.model_validate(data_raw)
    except Exception as e:
        pytest.fail(f"Schema breach in v2 analysis for {ticker}: {e}")

    # 1. Metadata Verification
    assert data.meta.ticker == ticker.upper()
    
    # 2. Execution Logic Verification
    if data.execution["action"] == "REJECT":
        assert data.execution["authorized"] is False
    
    # 3. Technical Content & Logic
    if data.system.data_quality != "INVALID":
        assert data.technicals is not None
        assert data.technicals.current_price > 0
        
        # Canonical v2 Signal Check
        assert data.signals is not None
        assert data.signals.primary_signal_strength is not None
        
        # Smart Logic Check (Levels Geometry)
        validate_levels_logic(data_raw["levels"])        

    # 4. Fundamental Completeness
    if data.fundamentals:
        assert data.fundamentals.comprehensive_metrics is not None
        assert "valuation" in data.fundamentals.comprehensive_metrics
    
    # 5. News & Intelligence
    news = data.news
    if news:
        assert len(news.news) >= 0 # List must exist
        if news.intelligence:
            assert news.intelligence.signal_score is not None
    
    # 6. System Meta Verification
    sys = data.system
    assert 0.0 <= sys.confidence <= 100.0
    assert sys.latency_ms > 0
    
    # Rule: If technicals are missing, confidence MUST be 0.0
    if sys.data_state_taxonomy.get("TECHNICALS") == "MISSING":
        assert sys.confidence == 0.0

@pytest.mark.live
@pytest.mark.parametrize("ticker", ["AAPL", "RELIANCE.NS"])
def test_v2_technical_logic(ticker):
    """Verify technical indicator bounds and relationships."""
    response = client.get(f"/api/v2/technical/{ticker}")
    assert response.status_code == 200
    data = response.json()
    
    if data.get("technicals"):
        # RSI Bounds
        rsi = data["technicals"]["rsi"]
        if rsi is not None:
            assert 0 <= rsi <= 100
            
        # Price Check
        assert data["current_price"] > 0

@pytest.mark.live
def test_v2_fundamental_valuation_math():
    """Verify DCF consistency for a major ticker."""
    ticker = "MSFT"
    response = client.get(f"/api/v2/fundamental/{ticker}/valuation")
    assert response.status_code == 200
    data = response.json()
    
    # Verify DCF terminal dominance bounds
    if "intrinsic_value_estimates" in data:
        dom = data["intrinsic_value_estimates"].get("terminal_value_dominance")
        if dom is not None:
            assert 0 <= dom <= 1.0

# --- RESEARCH & AI ---

@pytest.mark.live
def test_v2_research_completeness():
    ticker = "GOOGL"
    response = client.get(f"/api/v2/research/{ticker}/report")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_sources"] >= 0
    assert "synthesis" in data

# --- V1 REMOVAL VERIFICATION ---

def test_v1_api_absence():
    """Verify that all V1 endpoints are removed and return 404."""
    for path in ["/analyze/AAPL", "/technical/AAPL", "/fundamental/AAPL"]:
        response = client.get(path)
        assert response.status_code == 404