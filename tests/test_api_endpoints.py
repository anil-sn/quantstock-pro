import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

@pytest.mark.parametrize("ticker", ["AAPL", "TSLA"])
def test_technical_endpoint(ticker):
    print(f"\nTesting /api/v2/technical/{ticker}...")
    start = time.time()
    response = client.get(f"/api/v2/technical/{ticker}")
    latency = time.time() - start
    
    assert response.status_code == 200
    data = response.json()
    assert "horizons" in data
    assert latency < 15.0 # Institutional benchmark

@pytest.mark.parametrize("ticker", ["AAPL"])
def test_fundamental_endpoint(ticker):
    print(f"\nTesting /api/v2/fundamental/{ticker}...")
    response = client.get(f"/api/v2/fundamental/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "valuation" in data["comprehensive_metrics"]

@pytest.mark.parametrize("ticker", ["MSFT"])
def test_news_endpoint(ticker):
    print(f"\nTesting /api/v2/news/{ticker} (Unified Sources)...")
    response = client.get(f"/api/v2/news/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["news"]) > 0
    assert "intelligence" in data

@pytest.mark.parametrize("ticker", ["AAPL"])
def test_research_endpoint(ticker):
    print(f"\nTesting /api/v2/research/{ticker}/report (Deep Research)...")
    response = client.get(f"/api/v2/research/{ticker}/report")
    assert response.status_code == 200
    data = response.json()
    assert "synthesis" in data

@pytest.mark.parametrize("ticker", ["AAPL"])
def test_analyze_orchestrator(ticker):
    print(f"\nTesting /api/v2/analysis/{ticker} (The Brain)...")
    response = client.get(f"/api/v2/analysis/{ticker}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify v2 High-Level Blocks
    assert "meta" in data
    assert "execution" in data
    # Note: v2 AnalysisResponse does not have signals/levels at top level, 
    # they are within technicals or execution dict
    assert data["meta"]["ticker"] == ticker