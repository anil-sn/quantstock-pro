# QuantStock-Pro: Institutional Quantitative Analysis API

Advanced stock analysis platform that synthesizes multi-vendor market data with high-fidelity AI narrative synthesis.

## 🚀 Key Features
- **API v2.0 Architecture**: Modern, versioned, and resource-oriented REST API.
- **Dual-Engine Pipeline**: 
    - **Fast Path**: Deterministic, rule-based gating (<500ms).
    - **Slow Path**: AI-synthesized evidentiary narrative using Google Gemini.
- **Institutional Guardrails**: ATR-based risk sizing, confidence capping, and sector-relative scoring.
- **Multi-Vendor Failover**: Automatic fallback between Polygon.io and YahooFinance.
- **Forensic Audit Logs**: Granular payload and event tracing for every decision.

## 🛠️ Installation & Setup

### 1. Requirements
- Python 3.12+
- `uv` (Fastest Python package manager)

### 2. Quick Start
```bash
# Clone and install dependencies
uv pip install -e ".[dev]"

# Configure environment
cp .env_example .env
# Edit .env with your keys (GEMINI_API_KEY is required)

# Run the API
uvicorn app.main:app --reload
```

## 🧪 Testing Standard (Highest Grade)
The system is verified with a comprehensive suite of high-fidelity tests.

```bash
# Run all tests (Unit, Integration, and Live Forensics)
uv run env PYTHONPATH=. pytest -v
```

## 📡 API v2.0 Endpoints

### Service Status
- `GET /api/v2/health`: System health and component status.
- `GET /api/v2/status`: Service metrics and environment data.
- `GET /api/v2/limits`: Current rate limit usage.

### Stock Analysis
- `GET /api/v2/analysis/{ticker}`: Flagship multi-horizon report.
- `POST /api/v2/analysis/bulk`: Async batch analysis for multiple tickers.
- `GET /api/v2/analysis/{ticker}/technical`: Technical-only slice.
- `GET /api/v2/analysis/{ticker}/fundamental`: Fundamental-only slice.
- `GET /api/v2/analysis/{ticker}/execution`: Signals and entry/exit levels.

### Technical & Fundamental Sensors
- `GET /api/v2/technical/{ticker}`: Multi-horizon technical indicators.
- `GET /api/v2/technical/{ticker}/{interval}`: Specific interval technicals (1d, 1h, 15m).
- `GET /api/v2/fundamental/{ticker}`: Deep fundamental valuation (DCF).
- `GET /api/v2/fundamental/{ticker}/valuation`: Valuation models only.

### AI, News & Context
- `POST /api/v2/research/{ticker}`: Trigger autonomous research loops (Async).
- `GET /api/v2/news/{ticker}`: Signal-aware news intelligence.
- `GET /api/v2/context/{ticker}`: Smart money context (Insiders/Options).

---
*For full detailed documentation, see the [docs/](docs/) directory.*