# QuantStock-Pro: File Map & Functionality Reference

## Core Application (`app/`)

### 1. Orchestration & API
*   **`app/main.py`**: Entry point for the FastAPI application; configures middleware, routes, and exception handlers.
*   **`app/api.py`**: Defines API endpoints (`/analyze`, `/technical`, etc.) and routes requests to services.
*   **`app/service.py`**: The central brain (`STierTradingSystem`) that orchestrates technicals, fundamentals, news, and AI to produce trading decisions. Implements the **Fast Path / Slow Path** logic.
*   **`app/models.py`**: Defines all Pydantic data models, Enums, and schemas used across the platform for type safety and validation.
*   **`app/settings.py`**: Manages global configuration, environment variables, API keys, and system thresholds.
*   **`app/middleware.py`**: Implements security layers (API Key auth) and performance controls (Rate Limiting).
*   **`app/logger.py`**: structured logging utility for tracking pipeline events and debugging.

### 2. Technical Analysis Engine
*   **`app/technicals.py`**: Facade/Orchestrator for the technical analysis module (wraps indicators and scoring).
*   **`app/technicals_indicators.py`**: Calculates raw technical indicators (RSI, MACD, ADX, Bollinger Bands) using `pandas-ta` with strict data validation.
*   **`app/technicals_scoring.py`**: "Probabilistic Edge Engine" that normalizes indicators into weighted scores (Trend, Momentum, Volatility) and an overall signal.

### 3. Fundamental Analysis Engine
*   **`app/fundamentals.py`**: Orchestrates fetching and processing of fundamental data.
*   **`app/fundamentals_fetcher.py`**: Handles raw data ingestion for financial statements and company info with fallbacks for international stocks.
*   **`app/fundamentals_analytics.py`**: performs advanced quantitative analytics (DCF Valuation, Peer Benchmarking, Growth Trends).
*   **`app/fundamentals_scoring.py`**: Calculates a composite "Quality Grade" for a company based on profitability, health, and growth metrics.
*   **`app/fundamentals_rules.py`**: Contains qualitative inference rules for interpreting fundamental data.

### 4. Intelligence & Research
*   **`app/ai.py`**: Integrates with Google Gemini to synthesize multi-horizon investment theses. Implements the **Slow Path** with a circuit breaker.
*   **`app/news_fetcher.py`**: Aggregates news from multiple sources (RSS, APIs).
*   **`app/news_intelligence.py`**: Filters news noise, scores sentiment, and detects "Narrative Traps".
*   **`app/context.py`**: Fetches "Smart Money" context: Insider Trading activity and Options Market sentiment.
*   **`app/research/`**: Deep research agent for iterative web searching and evidentiary synthesis.

### 5. Execution & Governance
*   **`app/governor.py`**: `SignalGovernor` enforces strict trading rules and checks data integrity.
*   **`app/risk.py`**: `RiskEngine` calculates safe position sizing and capital-at-risk based on volatility.
*   **`app/executor.py`**: `TradeExecutor` calculates precise trade execution levels (Entry Zone, Stop Loss, Take Profit).
*   **`app/market_data.py`**: Handles async stock data ingestion (OHLCV) with caching.

## Documentation (`docs/`)
*   **`docs/DESIGN.md`**: Architectural philosophy and execution model.
*   **`docs/API_REFERENCE.md`**: Detailed endpoint documentation.
*   **`docs/THE_COMPLETE_FRAMEWORK.md`**: The comprehensive trading rules and strategy constitution.
*   **`docs/TODO.md`**: Chronological log of changes, tasks, and roadmap.
