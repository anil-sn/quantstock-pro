# QuantStock-Pro: Code Structure & Function Map

This document serves as a navigation guide for the institutional-grade trading platform.

## Core Application (`app/`)

### `models.py`
- **Purpose**: Defines the data contract for the entire system.
- **Key Symbols**: `AdvancedStockResponse`, `TechnicalStockResponse`, `TradeSetup`, `PipelineState`, `NewsIntelligence`.

### `service.py` (The S-Tier Orchestrator)
- `analyze_stock(ticker, mode)`: High-level orchestrator that executes Technical, Fundamental, and News analysis in parallel.
- `get_technical_analysis(ticker)`: Multi-horizon (Intraday, Swing, Positional, Longterm) parallel analysis.
- `STierTradingSystem`: Governance layer for pre-screening and final trade permission.

### `technicals/` (Calculated independently)
- `technicals_indicators.py`: Calculates RSI, MACD, ADX, Bollinger Bands with strict null handling.
- `technicals_scoring.py`: Normalizes indicators into a weighted algorithmic score (-100 to +100).

### `fundamentals/` (Quantitative deep-dive)
- `fundamentals.py`: Orchestrates fundamental analysis.
- `fundamentals_analytics.py`: Implements Intrinsic Valuation (DCF, Graham) and Peer benchmarking.
- `fundamentals_scoring.py`: Calculates the Composite Quality Grade.

### `news_intelligence.py` (The Noise Filter)
- `NewsIntelligenceEngine`: Classifies news headlines into "Institutional Signals" or "Retail Noise" to detect Narrative Traps.

### `ai.py` (The Brain)
- `interpret_advanced(...)`: Aggregates all quantitative outputs into a cohesive multi-horizon investment thesis using Gemini Pro.

### `governor.py` (Security & Rules)
- `SignalGovernor`: Enforces trading framework rules (e.g., Insider Selling vetoes) and validates data integrity.

### `market_data.py` (The Sensor)
- `fetch_stock_data(...)`: Async, cached ingestion of OHLCV and metadata from YFinance.

## Documentation (`docs/`)
- `FILE_MAP.md`: Master file list.
- `PROJECT_STRUCTURE.md`: High-level architecture.
- `THE_COMPLETE_FRAMEWORK.md`: The 100-page trading constitution.
- `TODO.md`: Implementation history and roadmap.