# Project Structure & Architecture: QuantStock Pro

## Core Architecture (S-Tier System)
The system operates on a multi-layered sensor and scoring architecture designed for institutional-grade quantitative stock analysis.

### Layer 0: Pre-Screen & Governance (`app/governor.py`)
- **Veto Logic**: Immediate rejection based on "Rule 0" (Insider Sells, Earnings Proximity).
- **Integrity Gating**: Blocks trades if critical sensors (RSI, MACD) are missing.

### Layer 1: Sensors (`app/market_data.py`, `app/fundamentals_fetcher.py`)
- **Multi-Vendor Ingestion**: `ProviderFactory` manages failover (Polygon -> Yahoo).
- **Historical Data**: Fetches OHLCV across Intraday, Swing, Positional, and Longterm horizons.

---

## File Map & Relationships

### Entry Points & API
- `app/main.py`: Core FastAPI initialization; mounts v2 router.
- `app/api_v2.py`: The modern, resource-oriented API specification (Version 2.0.0).
- `app/models_v2.py`: Versioned schemas for the 2.0 interface.

### Core Orchestration
- `app/service.py`: `QuantitativeTradingSystem` class manages the end-to-end analysis lifecycle.
- `app/ai.py`: Gemini LLM interface; handles structured Markdown synthesis and schema repair.

### Analytical Engines
- `app/technicals_indicators.py`: Robust indicator calculation with NaN resilience.
- `app/fundamentals_analytics.py`: Quantitative modeling (DCF, Graham, Peer Benchmarking).
- `app/research/engine.py`: Iterative Deep Research agent for fact-finding.

---

## Decisions & Data Flow
1. **Request**: Incoming `GET /api/v2/analysis/{ticker}`.
2. **Analysis**: Service layer orchestrates Layer 0 (Governance) -> Layer 1 (Sensors) -> Layer 2 (Scoring).
3. **Synthesis**: If successful, AI synthesizes a professional narrative report in Markdown.
4. **Response**: `AnalysisResponse` (JSON) returned with nested `executive_summary`.
