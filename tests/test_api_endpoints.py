import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

@pytest.mark.parametrize("ticker", ["AAPL", "TSLA"])
def test_technical_endpoint(ticker):
    print(f"\nTesting /technical/{ticker}...")
    start = time.time()
    response = client.get(f"/technical/{ticker}")
    latency = time.time() - start
    
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == ticker
    assert "overview" in data
    assert "technicals" in data
    assert "algo_signal" in data
    assert "horizons" in data
    assert latency < 15.0 # Institutional benchmark

@pytest.mark.parametrize("ticker", ["AAPL"])
def test_fundamental_endpoint(ticker):
    print(f"\nTesting /fundamentals/{ticker}...")
    response = client.get(f"/fundamentals/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "valuation" in data["comprehensive_metrics"]

@pytest.mark.parametrize("ticker", ["MSFT"])
def test_news_endpoint(ticker):
    print(f"\nTesting /news/{ticker} (Unified Sources)...")
    response = client.get(f"/news/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["news"]) > 0
    assert "intelligence" in data
    # Verify Google News presence (publishers other than Yahoo)
    publishers = [n["publisher"] for n in data["news"]]
    print(f"Publishers found: {set(publishers)}")

@pytest.mark.parametrize("ticker", ["AAPL"])
def test_research_endpoint(ticker):
    print(f"\nTesting /research/{ticker} (Deep Research)...")
    response = client.get(f"/research/{ticker}")
    assert response.status_code == 200
    data = response.json()
    assert "synthesis" in data
    assert len(data["iterations"]) >= 1
    assert data["total_sources"] > 0
    assert "diversity_metrics" in data

@pytest.mark.parametrize("ticker", ["AAPL"])
def test_analyze_orchestrator(ticker):
    print(f"\nTesting /analyze/{ticker} (The Brain)...")
    response = client.get(f"/analyze/{ticker}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify High-Level Blocks
    assert "meta" in data
    assert "execution" in data
    assert "signals" in data
    assert "levels" in data
    assert "context" in data
    assert "human_insight" in data
    assert "system" in data
    
    # Verify Machine Execution Data
    assert "action" in data["execution"]
    assert "valid_until" in data["execution"]
    assert "risk_limits" in data["execution"]
    
    # Verify Signals
    assert "primary_signal_strength" in data["signals"]
    assert "components" in data["signals"]
    
    # Verify Temporal and Performance Context
    assert "latency_ms" in data["system"]
    assert "next_update" in data["system"]
    assert "layer_timings" in data["system"]
    
    # Verify Levels
    assert "current" in data["levels"]
    assert len(data["levels"]["support"]) >= 0
    
    print(f"Latency: {data['system']['latency_ms']:.2f}ms")
    print(f"Action: {data['execution']['action']}")
