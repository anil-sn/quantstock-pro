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
uv run env PYTHONPATH=. pytest -v --run-live
```

## 📡 API v2.0 Quick Reference (Testing)

Base URL: `http://127.0.0.1:8000`
Swagger URL : `http://127.0.0.1:8000/docs`

### 1. Service Status & Control
| Resource | Exact URL for Testing |
| :--- | :--- |
| **Health** | `GET http://127.0.0.1:8000/api/v2/health` |
| **Status** | `GET http://127.0.0.1:8000/api/v2/status` |
| **Limits** | `GET http://127.0.0.1:8000/api/v2/limits` |
| **Cache Purge** | `DELETE http://127.0.0.1:8000/api/v2/cache/AAPL` |

### 2. Comprehensive Analysis (The Brain)
| Resource | Exact URL for Testing |
| :--- | :--- |
| **Full Report** | `GET http://127.0.0.1:8000/api/v2/analysis/AAPL?mode=full&include_ai=true` |
| **Bulk (POST)** | `POST http://127.0.0.1:8000/api/v2/analysis/bulk` |
| **Technical Slice** | `GET http://127.0.0.1:8000/api/v2/analysis/AAPL/technical` |
| **Fundamental Slice** | `GET http://127.0.0.1:8000/api/v2/analysis/AAPL/fundamental` |
| **Execution Slice** | `GET http://127.0.0.1:8000/api/v2/analysis/AAPL/execution` |

### 3. Technical Sensors
| Resource | Exact URL for Testing |
| :--- | :--- |
| **All Horizons** | `GET http://127.0.0.1:8000/api/v2/technical/AAPL` |
| **Trading Signals** | `GET http://127.0.0.1:8000/api/v2/technical/AAPL/signals` |
| **Price Levels** | `GET http://127.0.0.1:8000/api/v2/technical/AAPL/levels` |
| **Interval (1h)** | `GET http://127.0.0.1:8000/api/v2/technical/AAPL/1h` |

### 4. Fundamental Sensors
| Resource | Exact URL for Testing |
| :--- | :--- |
| **Complete Report** | `GET http://127.0.0.1:8000/api/v2/fundamental/AAPL` |
| **Valuation (DCF)** | `GET http://127.0.0.1:8000/api/v2/fundamental/AAPL/valuation` |
| **Quality Grade** | `GET http://127.0.0.1:8000/api/v2/fundamental/AAPL/quality` |
| **Ratios** | `GET http://127.0.0.1:8000/api/v2/fundamental/AAPL/ratios` |

### 5. News & Intelligence
| Resource | Exact URL for Testing |
| :--- | :--- |
| **All News** | `GET http://127.0.0.1:8000/api/v2/news/AAPL` |
| **Signal Impacts** | `GET http://127.0.0.1:8000/api/v2/news/AAPL/signal` |
| **Sentiment Analysis** | `GET http://127.0.0.1:8000/api/v2/news/AAPL/sentiment` |
| **Trending Topics** | `GET http://127.0.0.1:8000/api/v2/news/AAPL/trending` |

### 6. AI & Research
| Resource | Exact URL for Testing |
| :--- | :--- |
| **Initiate Research** | `POST http://127.0.0.1:8000/api/v2/research/AAPL` |
| **Research Status** | `GET http://127.0.0.1:8000/api/v2/research/AAPL/status` |
| **Final Report** | `GET http://127.0.0.1:8000/api/v2/research/AAPL/report` |
| **Ad-Hoc (POST)** | `POST http://127.0.0.1:8000/api/v2/ai/analyze` |
| **Explain Signal** | `GET http://127.0.0.1:8000/api/v2/ai/explain/rsi_oversold` |

### 7. Market Context (Smart Money)
| Resource | Exact URL for Testing |
| :--- | :--- |
| **Holistic Context** | `GET http://127.0.0.1:8000/api/v2/context/AAPL` |
| **Analyst Ratings** | `GET http://127.0.0.1:8000/api/v2/context/AAPL/analysts` |
| **Insider Activity** | `GET http://127.0.0.1:8000/api/v2/context/AAPL/insiders` |
| **Options Sentiment** | `GET http://127.0.0.1:8000/api/v2/context/AAPL/options` |
| **Institutional** | `GET http://127.0.0.1:8000/api/v2/context/AAPL/institutions` |

### 8. Real-Time Streaming
| Resource | Exact URL for Testing |
| :--- | :--- |
| **Signal Stream** | `GET http://127.0.0.1:8000/api/v2/stream/AAPL/signals` |
| **Live Analysis** | `WS ws://127.0.0.1:8000/api/v2/ws/analysis` |
| **Live Levels** | `WS ws://127.0.0.1:8000/api/v2/ws/levels` |

---
*For full detailed documentation, see the [docs/](docs/) directory.*
