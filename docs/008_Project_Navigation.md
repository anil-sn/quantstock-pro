# Project Navigation: QuantStock-Pro

This document serves as a guide to the codebase structure and key functionalities to ensure precise modifications.

## Core Application (`app/`)

### Foundation & Orchestration
- **`main.py`**: Application entry point and health check endpoints.
- **`service.py`**: The core orchestrator. Contains `QuantitativeTradingSystem` and the `analyze_stock` function which integrates all layers.
- **`settings.py`**: Configuration management using Pydantic `BaseSettings`.
- **`logger.py`**: `PipelineLogger` for structured event and payload logging.
- **`exceptions.py`**: Centralized custom exception definitions (SensorError, DataIntegrityError, etc.).

### Data Acquisition & Providers (`app/providers/`)
- **`base.py`**: `BaseDataProvider` abstract base class defining the interface for data providers.
- **`factory.py`**: `ProviderFactory` for dynamic provider instantiation and failover logic.
- **`yahoo.py`**: `YahooProvider` for fetching price history and ticker info via yfinance.
- **`polygon.py`**: `PolygonProvider` for institutional-grade data via Polygon.io.
- **`market_data.py`**: Utility functions for fetching raw OHLCV data.

### Intelligence & Analytics
- **`technicals_indicators.py`**: Calculates advanced technical indicators (RSI, MACD, etc.).
- **`technicals_scoring.py`**: `calculate_algo_signal` converts technical data into actionable signals.
- **`fundamentals_fetcher.py`**: Retrieves raw financial statements and growth metrics.
- **`fundamentals_analytics.py`**: Advanced financial math (DCF, Graham Number, Sloan Ratio, Kelly Criterion).
- **`fundamentals_scoring.py`**: Grades business models and quality, generates investment theses.
- **`fundamentals_rules.py`**: Derives qualitative inferences and risk assessments from data.
- **`news_fetcher.py`**: `UnifiedNewsFetcher` aggregates news from multiple APIs and web sources.
- **`news_intelligence.py`**: `NewsIntelligenceEngine` for sentiment scoring and headline analysis.
- **`ai.py`**: Handles AI-driven interpretation, prompt construction, and deterministic fallback logic.

### Governance & Execution
- **`governor.py`**: `SignalGovernor` and `UnifiedRejectionTracker` enforce trading rules and data integrity (Veto logic).
- **`risk.py`**: `RiskEngine` for position sizing and capital-at-risk calculations.
- **`executor.py`**: `TradeExecutor` for calculating precise entry/exit levels and trade scoring.
- **`context.py`**: Extracts market context (analysts, insiders, options sentiment).
- **`cache.py`**: `CacheManager` for Redis-based distributed caching and performance optimization.

### Research Layer (`app/research/`)
- **`engine.py`**: `ResearchEngine` for multi-iteration deep research on tickers.
- **`diversity.py`**: `SourceDiversityManager` ensures balanced information gathering.
- **`repository.py`**: `FindingsRepository` stores and formats research data for AI synthesis.

### API & Models
- **`api_v2.py`**: Implementation of V2 REST endpoints and WebSockets.
- **`models.py`**: Comprehensive Pydantic models for V1 and core data structures.
- **`models_v2.py`**: Pydantic models specifically for V2 API contracts.

## Tests (`tests/`)
- **`test_granular_pipeline.py`**: Step-by-step verification of the data pipeline.
- **`test_core_logic.py`**: Validation of algorithmic and mathematical components.
- **`test_api_v2.py` / `test_api_endpoints.py`**: REST API contract verification.
- **`test_ai_integration.py`**: Testing AI analysis and fallback resilience.
- **`test_real_world_forensics.py`**: Testing the system against complex real-world data scenarios.
- **`test_response_integrity.py`**: Deep, exhaustive validation of API response schemas and logical invariants.
