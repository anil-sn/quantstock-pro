# QuantStock-Pro: Code Structure & Functionalities

## 🏗️ Core Architecture
The system follows a multi-layered analytical pipeline:
- **Layer 0 (Pre-Screen)**: Regulatory and event-based filtering.
- **Layer 1 (Sensors)**: Multi-vendor data ingestion (Price, Fundamentals, News, Context).
- **Layer 2 (Scoring)**: Quantitative edge engines (Technicals, Algo Signals, Quality Grades).
- **Layer 3 (Intelligence)**: AI Synthesis and Narrative grounding.
- **Layer 4 (Execution)**: Risk-adjusted level calculation and position sizing.

---

## 📂 app/ (Source Root)

### `main.py`
- Entry point for FastAPI. Orchestrates the inclusion of both **v1** and **v2** API routers.
- Configures global middleware (Rate Limiting, Security, Telemetry).

### `api_v2.py` (Versioned Endpoints)
- Primary interface for current generation clients.
- Implements resource-oriented routing for analysis, sensors, and status.

### `models_v2.py` (Enhanced Schemas)
- Defines versioned response models (`AnalysisResponse`, `HealthResponse`).
- Supports strict Pydantic validation for the 2.0.0 API specification.

### `service.py` (The Brain)
- `QuantitativeTradingSystem`: Central orchestrator.
- Manages the **Fast Path** (deterministic rejections) and **Slow Path** (LLM synthesis) logic.

### `ai.py` (Narrative Engine)
- `interpret_advanced()`: Gemini LLM interface.
- Uses **Optimized Evidence-Based Prompting** to generate structured Markdown reports.
- Includes **Schema Repair** logic to handle model hallucinations.

### `technicals_indicators.py` & `technicals_scoring.py`
- Implementation of the technical sensor layer. 
- Features **NaN Forward-Filling** and **CCI Poison Detection** for institutional-grade reliability.

### `fundamentals_analytics.py` & `fundamentals_scoring.py`
- Implements the fundamental sensor layer.
- Includes **3-Stage DCF**, **Graham Number**, and **Sector Distance** benchmarking.

### `market_data.py` & `providers/`
- Multi-vendor failover ingestion (Polygon.io primary, YahooFinance fallback).

---

## 📂 app/research/
- Iterative web research agent for fact-finding from primary sources.
- Centralized `repository.py` for fact deduplication and citation tracking.