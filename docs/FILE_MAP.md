# File Map

## Root
*   `app/main.py`: Entry point for the FastAPI application.
*   `app/api.py`: API Router defining all endpoints (`/analyze`, `/technical`, `/fundamentals`, `/news`, `/context`).
*   `app/service.py`: Central orchestrator (`analyze_stock`) and domain-specific analysis services (`get_technical_analysis`, etc.).
*   `app/models.py`: Pydantic models and Enums for the entire platform.
*   `app/technicals.py`: Facade for technical analysis module.
*   `app/technicals_indicators.py`: Implementation of raw technical indicator calculations with data validation.
*   `app/technicals_scoring.py`: Algorithmic scoring engine for technical signals.
*   `app/news_intelligence.py`: News signal & noise filtration engine.
*   `app/ai.py`: Gemini AI integration for multi-horizon synthesis.
*   `app/market_data.py`: Async data ingestion layer (YFinance wrapper).
*   `app/fundamentals.py`: Orchestrator for fundamental analysis and raw news fetching.
*   `app/fundamentals_fetcher.py`: Data ingestion for financial statements.
*   `app/fundamentals_rules.py`: Qualitative inference rules for fundamentals.
*   `app/fundamentals_scoring.py`: Composite scoring engine for business quality.
*   `app/fundamentals_analytics.py`: Advanced quant analytics (DCF, Peer Stats, Trends).
*   `app/context.py`: Smart money and market context fetcher.
*   `app/governor.py`: Rule enforcement and data integrity governor.
*   `app/middleware.py`: Security and performance middleware (Rate Limiting, API Key).
*   `app/settings.py`: Global configuration and thresholds.

## Function Signatures

### `app/service.py`
*   `class STierTradingSystem`:
    *   `pre_screen(self, market_context: Optional[MarketContext]) -> Optional[TradingDecision]`
    *   `analyze(self, technicals: Technicals, algo_signal: AlgoSignal, market_context: Optional[MarketContext], fundamentals: Any) -> TradingDecision`
*   `get_technical_analysis(ticker: str) -> TechnicalStockResponse`: Multi-horizon parallel analysis.
*   `analyze_stock(ticker: str, mode: Any = "all") -> AdvancedStockResponse`: Global orchestrator.

### `app/technicals_indicators.py`
*   `calculate_advanced_technicals(df: pd.DataFrame) -> Technicals`: Validated indicator calculation.

### `app/technicals_scoring.py`
*   `calculate_algo_signal(technicals: Technicals) -> AlgoSignal`: Normalized algorithmic scoring.

### `app/news_intelligence.py`
*   `NewsIntelligenceEngine.analyze_feed(ticker: str, news: List[NewsItem]) -> NewsIntelligence`: Noise filtration.

### `app/ai.py`
*   `interpret_advanced(...) -> AIAnalysisResult`: Gemini-based aggregator.

### `app/context.py`
*   `get_market_context(ticker: str) -> MarketContext`: Smart money context (Insiders, Options).