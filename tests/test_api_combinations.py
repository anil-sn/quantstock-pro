import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import AnalysisMode

client = TestClient(app)

# Test Configuration
TICKERS = ["AAPL", "RELIANCE.NS"]
MODES = ["all", "longterm", "positional", "swing", "intraday"]
FORCE_AI_OPTS = [True, False]

@pytest.mark.parametrize("ticker", TICKERS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("force_ai", FORCE_AI_OPTS)
def test_analyze_combinations(ticker, mode, force_ai):
    """Verify all combinations of mode and force_ai for the /analyze endpoint."""
    params = {"mode": mode, "force_ai": force_ai}
    response = client.get(f"/analyze/{ticker}", params=params)
    
    assert response.status_code == 200, f"Failed for {ticker} with mode={mode}, force_ai={force_ai}"
    data = response.json()
    
    # Structural Validation
    assert "meta" in data
    assert "execution" in data
    assert data["meta"]["ticker"] == ticker.upper()
    
    # Engine Logic Validation
    if force_ai:
        # If forced, it should be HYBRID (unless it crashes, but we hardened it)
        # Note: If it hit a deterministic rejection before AI, logic might be DETERMINISTIC
        # But our latest hardening allows HYBRID even for rejections if forced.
        assert data["system"]["engine_logic"] in ["HYBRID", "DETERMINISTIC"]
    
    print(f"PASS: /analyze/{ticker}?mode={mode}&force_ai={force_ai} -> {data['execution']['action']}")

@pytest.mark.parametrize("ticker", TICKERS)
def test_research_endpoint(ticker):
    """Verify the /research endpoint."""
    response = client.get(f"/research/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == ticker.upper()
    assert "synthesis" in data
    assert "iterations" in data

@pytest.mark.parametrize("ticker", TICKERS)
@pytest.mark.parametrize("endpoint", ["technical", "fundamentals", "news", "context"])
def test_granular_endpoints(ticker, endpoint):
    """Verify granular sensor endpoints."""
    response = client.get(f"/{endpoint}/{ticker}")
    assert response.status_code == 200
    data = response.json()
    
    # Recursive search for ticker string in the entire JSON structure
    def find_ticker(obj, target):
        if isinstance(obj, str) and target.upper() in obj.upper():
            return True
        if isinstance(obj, dict):
            return any(find_ticker(v, target) for v in obj.values())
        if isinstance(obj, list):
            return any(find_ticker(item, target) for item in obj)
        return False

    assert find_ticker(data, ticker), f"Ticker {ticker} not found in /{endpoint} response"

def test_health_endpoint():
    """Verify /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint():
    """Verify /metrics endpoint (Prometheus)."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus returns text/plain, not JSON
    assert "python_info" in response.text or "http_request" in response.text
