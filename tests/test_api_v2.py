import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models_v2 import AnalysisMode, TimeInterval

client = TestClient(app)

# --- STATUS ENDPOINTS ---

def test_v2_health():
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "uptime_seconds" in response.json()

def test_v2_status():
    response = client.get("/api/v2/status")
    assert response.status_code == 200
    assert "engine_version" in response.json()

def test_v2_limits():
    response = client.get("/api/v2/limits")
    assert response.status_code == 200
    assert "rate_limit" in response.json()

# --- ANALYSIS ENDPOINTS ---

@pytest.mark.live
def test_v2_comprehensive_analysis():
    response = client.get("/api/v2/analysis/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "ai_insights" in data

@pytest.mark.live
def test_v2_analysis_subresources():
    # Recursive search for ticker string in the entire JSON structure
    def find_ticker(obj, target):
        if isinstance(obj, str) and target.upper() in obj.upper():
            return True
        if isinstance(obj, dict):
            return any(find_ticker(v, target) for v in obj.values())
        if isinstance(obj, list):
            return any(find_ticker(item, target) for item in obj)
        return False

    for res in ["technical", "fundamental", "execution"]:
        response = client.get(f"/api/v2/analysis/AAPL/{res}")
        assert response.status_code == 200
        assert find_ticker(response.json(), "AAPL")

# --- TECHNICAL ENDPOINTS ---

@pytest.mark.live
def test_v2_technical_granular():
    # 1. Signals
    assert client.get("/api/v2/technical/AAPL/signals").status_code == 200
    # 2. Levels
    assert client.get("/api/v2/technical/AAPL/levels").status_code == 200
    # 3. All
    assert client.get("/api/v2/technical/AAPL").status_code == 200
    # 4. Interval
    assert client.get("/api/v2/technical/AAPL/1h").status_code == 200

# --- FUNDAMENTAL ENDPOINTS ---

@pytest.mark.live
def test_v2_fundamental_granular():
    for sub in ["", "valuation", "quality", "ratios"]:
        path = f"/api/v2/fundamental/AAPL/{sub}".rstrip("/")
        response = client.get(path)
        assert response.status_code == 200
        assert len(response.json()) > 0

# --- NEWS & CONTEXT ---

@pytest.mark.live
def test_v2_news_granular():
    for sub in ["", "signal", "sentiment", "trending"]:
        path = f"/api/v2/news/AAPL/{sub}".rstrip("/")
        response = client.get(path)
        assert response.status_code == 200

@pytest.mark.live
def test_v2_context_granular():
    for sub in ["", "analysts", "insiders", "options", "institutions"]:
        path = f"/api/v2/context/AAPL/{sub}".rstrip("/")
        response = client.get(path)
        assert response.status_code == 200

# --- AI & RESEARCH ---

@pytest.mark.live
def test_v2_research_async():
    response = client.post("/api/v2/research/AAPL")
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.live
def test_v2_research_report():
    response = client.get("/api/v2/research/AAPL/report")
    assert response.status_code == 200
    assert "synthesis" in response.json()

def test_v2_ai_placeholders():
    assert client.post("/api/v2/ai/analyze", json={}).status_code == 200
    assert client.get("/api/v2/ai/explain/rsi").status_code == 200