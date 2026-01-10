# TODO: Immediate Survival Hotfixes & Architectural Overhaul

## ⚔️ Brutal Audit Remediation (v9.4.0-BRUTAL) - COMPLETED ✅

- [x] **Data Integrity Core**: Implemented "Stop the World" checks for critical missing data (Close, RSI, MACD).
- [x] **CCI Reconstruction**: Replaced flawed z-score outlier detection with robust hard-clamping to eliminate "CCI -4000" artifacts.
- [x] **Trend Following Alignment**: Switched Momentum scoring from mean-reversion (low RSI = high score) to trend-following logic (high RSI = high score).
- [x] **Neutral Trend Fix**: Resolved bug where Neutral trends were penalized as Bearish (-100).
- [x] **Override Elimination**: Removed arbitrary "Confluence Boost" (+/- 30 pts) to ensure monotonic scoring.
- [x] **Unit Standardization**: Normalized all momentum components (RSI, MACD, CCI) to consistent -100 to +100 scales before aggregation.

## 🌍 Multi-Horizon & Refactoring (v9.5.0) - COMPLETED ✅

- [x] **Technicals Module Split**: Refactored `technicals.py` into `technicals_indicators.py` and `technicals_scoring.py` for maintainability.
- [x] **Multi-Horizon Analysis**: Implemented parallel execution of Intraday (60m), Swing (1d), Positional (1wk), and Longterm (1mo) analysis in `get_technical_analysis`.
- [x] **Raw Data Exposure**: Added `raw_data` (OHLCV) and `horizons` (MultiHorizonSetups) to the API response for frontend/algo validation.

## 🛡️ Institutional Governance Overhaul (v9.6.0-GOVERNANCE) - COMPLETED ✅

- [x] **Two-Layer Architecture**: Implemented explicit separation between *Market State* (Layer 1) and *Trade Permission* (Layer 2).
- [x] **Regime Gating**: Added hard "Untradeable Object" checks (ATR > 3% + ADX < 20) to reject capital shredders before rules are even checked.
- [x] **Semantic Safety**: Renamed dangerous labels ("Bullish" -> "Positive Structure", "Accumulation" -> "High Activity") to prevent operator confusion.
- [x] **Continuous Momentum**: Replaced binary MACD scoring with continuous, volatility-aware normalization.
- [x] **Trend Integrity**: Enforced strict zeroing of Trend Score when ADX < 20 to prevent "phantom trend" signals.

## 🧮 Logic & Math Audit Remediation (v9.7.0-MATH) - COMPLETED ✅

- [x] **Early Exit Architecture**: Implemented `pre_screen()` to reject trades based on Market Context (e.g., Insider Selling) *before* expensive Technical Analysis is run.
- [x] **RSI Logic Fix**: Rewrote spaghetti boolean logic with standard Mean Reversion interpretation (<30 Oversold, >70 Overbought).
- [x] **Volume Scaling**: Switched from linear to robust scaling (1.0-2.0 ratio -> 0-100 score) with clamping.
- [x] **Trend Double-Counting**: Adjusted weights to prioritize Structure (80%) over MA Alignment (20%).
- [x] **Volatility Labeling**: Clarified scoring direction (Low Volatility = Positive Score = Safe/Stable).

## 🧠 AI Decoupling & Aggregation (v9.8.0-AI) - COMPLETED ✅

- [x] **AI Orchestrator**: Refactored `analyze_stock` to orchestrate parallel calls to Technical, Fundamental, and News services instead of running logic internally.
- [x] **Interface Decoupling**: Updated `interpret_advanced` (AI) to accept structured Pydantic response objects (`TechnicalStockResponse`, etc.) instead of raw data dicts.
- [x] **Service Isolation**: Ensured `get_technical_analysis` and `get_market_context` are the single sources of truth for their respective domains.
- [x] **Pre-Screening Integration**: Integrated `pre_screen` check into the orchestrator to skip AI costs for rejected trades.
- [x] **Governance Fix**: Exposed `check_insider_trading` in `SignalGovernor` to fix AttributeError in pre-screen.
- [x] **Import Fix**: Added missing `TrendDirection` import in `app/service.py` to fix NameError.
- [x] **Bug Fix**: Resolved `NameError: name 'adx_factor' is not defined` in `technicals_scoring.py`.
- [x] **Validation Fix**: Made `stop_loss`, `take_profit`, and `entry_zone` optional in `TradingDecision` model to resolve Pydantic validation errors during rejections.

## 🛡️ Pipeline & Architecture Audit Remediation (v9.9.0-TERMINAL) - COMPLETED ✅

- [x] **Terminal State Protocol**: Enforced `None` for technicals and signals when Pre-Screen rejects a trade. No more "zombie objects" with fake zeros.
- [x] **Model Hygiene**: Updated `TechnicalStockResponse` to allow optional technicals/signals. Added `RiskLevel.UNKNOWN`.
- [x] **Logic Cleanup**: Removed legacy dummy object construction in `analyze_stock` and `_process_horizon`.
- [x] **Verification**: Passed tests for Rejection Nulling and Raw Data Suppression.

## 🚀 Final Pipeline Optimization (v10.0.0-PRO) - COMPLETED ✅

- [x] **Global Pre-Screening**: Technical analysis now performs a unified pre-screen check before fetching horizon data, reducing network calls by 75% on rejected trades.
- [x] **Horizon Templating**: Optimized object creation by using a single rejection template for all timeframes.
- [x] **Strict Data Suppression**: Ensured `raw_data` is strictly `None` for rejected trades to optimize bandwidth and security.
- [x] **Integrity Consistency**: Resolved "Schrödinger's Data" paradox; valid data used for headers is now correctly marked as `DataIntegrity.VALID`.

## 📰 News Intelligence & Signal Filtration (v11.0.0-INTEL) - COMPLETED ✅

- [x] **Information Density Scorer**: Implemented headline-level classification to distinguish between "Institutional Signals" (Guidance, Earnings) and "Retail Noise" (Hype, Watchlists).
- [x] **Publisher Diversity Check**: Added automated detection of single-publisher concentration (e.g., 100% Yahoo Finance) to flag low-breadth news feeds.
- [x] **Narrative Trap Detector**: Implemented logic to warn when a news feed is dominated by price-following noise (>60% noise ratio + low diversity).
- [x] **Multi-Source Ingestion**: Integrated **Google News RSS** and **NewsAPI.org** to diversify sourcing and improve signal breadth.
- [x] **Audit Fix**: Verified remediation using the CALX news feed; correctly identified a 70% Noise Ratio and triggered a "Narrative Trap" warning.

## 🔬 Deep Research Agent (v12.0.0-RESEARCH) - COMPLETED ✅

- [x] **Iterative Search Orchestrator**: Implemented multi-stage research loops to move from retail news to primary source validation (SEC filings, transcripts).
- [x] **Source Diversity Audit**: Added automated classification of sources into Academic, Government, and Primary Corporate to detect media echo chambers.
- [x] **Findings Repository**: Built a centralized knowledge store that deduplicates facts across search iterations and maintains citation traceability.
- [x] **Evidentiary Synthesis**: Updated AI synthesis to use IEEE-style citations [1], linking every claim to a verified source URL.
- [x] **Research Agent Fixes**: Fixed `NameError` for `ResearchReport`, removed duplicate definitions in `models.py`, and updated the engine to support asynchronous search tools. Also fixed `NameError` for `SourceDiversity` in `engine.py`.
- [x] **Strict Grounding Protocol**: Implemented hallucination gating to skip synthesis when data is absent and hardened prompts to ensure claims are 100% evidentiary.

## 🏁 Project Finalization & Documentation - COMPLETED ✅

- [x] **Architecture Sync**: Updated `FILE_MAP.md` and `CODE_STRUCTURE_AND_FUNCTIONS.md` to reflect the modular technicals and research engine.
- [x] **E2E Validation Protocol**: Documented the sequential endpoint execution order in `README.md`.
- [x] **Strategic Audit Targets**: Added specific testing scenarios (`CALX`, `AAPL`) to the main README for institutional validation.
- [x] **Governance Hardening**: Implemented **Rule 4: Earnings Proximity** to block trading within 14 days of binary events.
- [x] **Confidence Intelligence**: Added "Evidence Gap" detection to penalize sentiment when primary analyst data is missing.
- [x] **Forensic Rich Logging**: Integrated `rich` library for high-fidelity terminal traces and implemented JSON payload logging for all sensors, AI prompts, and raw model outputs in `logs/pipeline.log`.
- [x] **Dependency Sync**: Resolved `ModuleNotFoundError` for `rich` and fixed `uv sync` package discovery errors by explicitly configuring `setuptools` in `pyproject.toml`.
- [x] **Hardened Reality Protocol (v14.0.0)**: Purged hardcoded "risk theater" placeholders (0.15%, 3% position) from rejections. Enforced a **Confidence Ceiling** where sub-horizon confidence cannot exceed global system confidence.
- [x] **Options & AI Veto**: Hard-blocked AI from proposing options strategies when primary sentiment data is absent. Corrected AI indicator semantics for Bollinger Band positioning.
- [x] **Institutional Risk Fix (v15.0.0)**: Corrected the Risk Math formula for capital at risk. Enforced a **Decision Singularity** across all AI horizons and a global **Confidence Ceiling** to prevent fraudulent certainty in sub-modules.

## 🚨 Immediate Survival Hotfixes (Next 24 Hours)

### Security & Safety
- [x] **SSL Verification**: Revert dangerous SSL bypass in `app/main.py`.
- [x] **Prompt Injection**: Sanitize `system_context` in `app/ai.py`.
- [x] **Rate Limiting**: Implement `RateLimiter` middleware in `app/api.py`.
- [x] **API Auth**: Add API Key authentication middleware.

### Performance
- [x] **Async Blocking**: Wrap `yfinance` calls in `run_in_threadpool` within `app/market_data.py` (and others if needed).
- [x] **Caching**: Implement in-memory cache (e.g., `async-lru` or `cachetools`) for market data and AI results to prevent cost explosion.

### Mathematical Foundation
- [x] **CCI Validation**: Replace absolute poison check with 3-Sigma statistical validation in `app/technicals.py`.
- [x] **Position Sizing**: Patch `_calculate_position_size` in `app/service.py` to include liquidity constraints and hard risk caps.
- [x] **Volatility Score**: Improved volatility score calculation in `app/technicals.py`.

## 🏗️ Architectural Refactor (Week 1)

### Modularization
- [x] Break `STierTradingSystem` (Monolith) in `app/service.py` into:
    - `RiskEngine` (Risk assessment, sizing)
    - `SignalGovernor` (Rules, Integrity)
    - `TradeExecutor` (Level calculation, Decision creation)
- [x] Resolve Circular Dependencies (if any persist).

### Unified Logic
- [x] **Rejection Consistency**: Ensure `Technical` and `Advanced` endpoints share exact rejection logic (Already largely addressed by `UnifiedRejectionTracker`, verify).
- [x] **Enum Unification**: Merge/Clean up `DataValidity`, `DataIntegrity` if redundant.

## 📉 Trading Strategy Refinements (Week 2+)

- [x] **Fundamentals Pipeline**: Implemented institutional-grade engine with derived ratios, lifecycle stages, and multi-factor scoring.
- [x] **News Decoupling**: Decoupled news into a standalone endpoint and logic layer.
- [x] **Data Integrity**: Added sanity checks for YFinance data in `app/fundamentals.py`.
- [ ] **Insider Intent**: Refine parsing to ignore tax-selling and pre-planned (10b5-1) trades.
- [ ] **Dynamic Stop Loss**: Adjust SL strategy based on Playbook (A/B) from framework.
- [ ] **Option Sentiment**: Refine PCR interpretation to distinguish hedging from direction.
- [ ] **Portfolio Risk**: Add correlation/beta checks and sector-relative scoring.
- [ ] **Backtesting**: Implement `BacktestEngine` to validate signals.

## 🏛️ Institutional-Grade Refactoring (v7.4.0)

- [x] **Harden Balance Sheet Scoring**: Implemented a sliding scale for net cash fortress bonuses (25% MC threshold).
- [x] **Margin Fragility Hard Cap**: Implemented a maximum quality score of 65 when operating margins are <50% of sector and FCF is declining.
- [x] **Risk-Adjusted DCF**: Added discount rate uplifts (2-4%) for companies with sub-10% operating margins to account for economic instability.
- [x] **Capital Efficiency Module**: Integrated ROIC and Invested Capital tracking into the analysis pipeline.
- [x] **Downside Scenarios**: Added Valuation Compression and Flat Growth scenarios to the scenario analysis engine.

## 🏛️ Institutional-Grade Rebuild (v9.2.0-FORENSIC) - CERTIFIED ✅

- [x] **Strict Forensic Data Gates**: Implemented `DATA_HOLD` triggers for accounting sign paradoxes (e.g., Positive NI vs Negative ROE).
- [x] **DCF Mathematical Kill-Switch**: Hard rejection of valuations where Terminal Dominance > 50% (Mathematical Ill-Posedness).
- [x] **Forensic FCF Quality**: Reclassified accounting-to-cash divergence as "Elevated Risk" with mandatory audit notes.
- [x] **Leadership Failure Penalty**: Integrated boardRisk/compensationRisk as non-negotiable composite score deductions.
- [x] **Monotonic Scenario Logic**: Fixed scenario price ordering and CAGR math to ensure negative EV is correctly represented.
- [x] **Temporal Synchronization**: Anchored all returns to a unified periodicity bridge to eliminate data entropy.

## 📈 Roadmap & Enhancements (v9.3.0+)

- [ ] **Statistical Refinement**: Deprecate pseudo-statistical Z-scores; replace with explicit Peer Distribution datasets, sample size (N), and variance attribution.
- [ ] **Monte Carlo Valuation**: Transition from 3-point scenario trees to 10,000-iteration probability distributions.
- [ ] **Convex Scoring**: Implement non-linear penalty functions for "Cliff Edge" risks (e.g., Debt/EBITDA > 4.0).

## 🏛️ Institutional-Grade Refactoring (v7.3.0)

- [x] **Revenue Growth Standardization**: Implemented actual YoY calculation from quarterly financials to cross-verify and replace inconsistent Yahoo fields.
- [x] **Data Provenance**: Added `last_updated` timestamps and explicit `data_provenance` metadata to the analysis response.
- [x] **Robust News Parsing**: Integrated `dateutil.parser` for reliable timestamp extraction across varying news source formats.
- [x] **Growth Durability**: Refined scoring to reward FCF-backed growth and penalize high-burn growth scenarios.
- [x] **Threshold Externalization**: Continued moving hardcoded analytical thresholds to `settings.py`.
- [x] **Production Hardening**: Integrated Sentry SDK for error tracking and enhanced the `/health` telemetry endpoint.
- [x] **Deployment Orchestration**: Created `deploy.sh` with automated syntax checks and health verification.

## 🏛️ Institutional-Grade Refactoring (v7.2.0)

- [x] **Double Scoring**: Resolved by computing `quality_score` once in `get_fundamentals` and storing it in the `FundamentalData` model.
- [x] **Circular Valuation**: Fixed Graham Number logic to use direct `book_value` or non-price-based proxies, eliminating market-price circularity.
- [x] **DCF Transparency**: Implemented `terminal_value_dominance` metric to flag valuations where >60% of PV is driven by terminal assumptions.
- [x] **Intuitive Analytics**: Refactored Peer Z-scores for P/E so that higher Z-scores correctly indicate better value (undervaluation).
- [x] **Linear Scoring**: Replaced binary margin penalties with slope-based scoring for profitability and growth.
- [x] **Advanced Risk Gating**: Integrated "Margin Compression" and "Negative FCF" checks into the multi-factor risk assessment.
- [x] **Scenario Integrity**: Linked base-scenario target prices to quantitative valuation outputs instead of investment horizon strings.

## 🏛️ Institutional-Grade Refactoring (v7.1.0)

- [x] **Valuation Hardening**: Replace heuristic DCF with a multi-stage model including margin convergence and sensitivity matrix.
- [x] **Earnings Normalization**: Fix Graham Number to handle negative EPS via normalized 3-year averages.
- [x] **Risk Integration**: Refactor Recommendation logic to use the Risk Score as a hard-gate/penalty (Unify Scoring & Risk).
- [x] **Base-Effect Correction**: Implement caps and semantic overrides for YoY % growth when denominators are near-zero.
- [x] **Statistical Rigor**: Update Peer Z-Score logic to use empirical variance or sector-specific standard deviations.
- [x] **Code Integrity**: Remove double-scoring calls in `fundamentals.py` and eliminate profitability floor hacks in `fundamentals_scoring.py`.
- [x] **Data Validation**: Implement a cross-metric consistency checker (e.g., Market Cap vs. Shares * Price).

## 🟡 Code Quality & Observability

- [ ] **Logging**: Add structured JSON logging throughout for deep debugging.
- [x] **Magic Numbers**: Externalized thresholds and constants to `app/settings.py`.
- [ ] **Error Handling**: Replace bare `except Exception: pass` with specific error handling.
