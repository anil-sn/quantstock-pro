# QuantStock-Pro API Reference

## Base URL
Defaults to `http://localhost:8000` (or your configured host/port).

## Authentication
All endpoints (except `/health`) require an API Key.
*   **Header**: `X-API-Key`
*   **Value**: Your configured `API_KEY` in `.env`.

## Endpoints

### 1. Comprehensive Analysis
**`GET /analyze/{ticker}`**

The flagship endpoint. Orchestrates Technicals, Fundamentals, News, and AI Synthesis into a single report. It employs a **Dual-Engine Architecture** (Fast Path/Slow Path) to guarantee low latency for critical decisions.

*   **Parameters**:
    *   `ticker` (path, string): Stock symbol (e.g., `AAPL`, `NVDA`).
    *   `mode` (query, string, default=`all`): Analysis mode.
        *   `all`: Full analysis including AI synthesis.
        *   `execution`: Fast Path only (deterministic decision, skip LLM).
        *   `intraday`: Skips deep fundamentals, focuses on short-term.

*   **Response**: `AdvancedStockResponse` (JSON) containing:
    *   `meta`: Traceability data (analysis_id, timestamps, version).
    *   `execution`: **Canonical Authority Block**. Contains the final `action`, `authorized` flag, and `vetoes`.
    *   `signals`: Normalized quantitative signals [-1, 1] across trend, momentum, expectancy, and valuation.
    *   `levels`: Execution levels (Support, Resistance, Value Zones) with strengths.
    *   `context`: Market regime classification and trend intensity.
    *   `human_insight`: AI-generated executive summary, conflicts, and scenarios (Slow Path).
    *   `system`: Performance metrics, layer timings, and data taxonomy.

### 2. Deep Research Agent
**`GET /research/{ticker}`**

Triggers the autonomous Deep Research Agent to perform iterative web searches, fact-finding, and synthesis.

*   **Parameters**:
    *   `ticker` (path, string): Stock symbol.

*   **Response**: `ResearchReport` (JSON) containing:
    *   `synthesis`: AI-written executive summary with IEEE citations.
    *   `iterations`: Details of search queries and findings per iteration.
    *   `diversity_metrics`: Audit of source types (Government, Academic, News) to detect bias.

### 3. Technical Analysis
**`GET /technical/{ticker}`**

Returns multi-horizon technical analysis (Intraday, Swing, Positional, Longterm) without AI synthesis or fundamentals.

*   **Parameters**:
    *   `ticker` (path, string): Stock symbol.

*   **Response**: `TechnicalStockResponse` (JSON).

### 4. Fundamental Analysis
**`GET /fundamentals/{ticker}`**

Returns deep-dive fundamental data, valuation models (DCF), and forensic quality scoring.

*   **Parameters**:
    *   `ticker` (path, string): Stock symbol.

*   **Response**: `AdvancedFundamentalAnalysis` (JSON).

### 5. News Intelligence
**`GET /news/{ticker}`**

Fetches recent news, filters noise, and provides sentiment analysis and "Narrative Trap" warnings.

*   **Parameters**:
    *   `ticker` (path, string): Stock symbol.

*   **Response**: `NewsResponse` (JSON).

### 6. Market Context
**`GET /context/{ticker}`**

Returns "Smart Money" data: Insider transactions and Options market sentiment (PCR, IV).

*   **Parameters**:
    *   `ticker` (path, string): Stock symbol.

*   **Response**: `MarketContext` (JSON).

### 7. System Health
**`GET /health`**

Returns system status, uptime, and version.

*   **Auth**: Public (No API Key required).
*   **Response**: JSON status object.