# Project Structure and Functionality Map

This document outlines the file structure of the `quantstock-pro` project and the specific responsibilities of each module.

## Root Directory

*   **`README.md`**: Project overview, installation, and usage guide.
*   **`THE_COMPLETE_FRAMEWORK.md`**: The "Constitution". Defines the trading strategy, risk management rules, and operational philosophy (S-Tier requirements).
*   **`pyproject.toml`**: Dependency management and build configuration (FastAPI, pandas-ta, yfinance, google-genai).
*   **`Evaluation.md`**: External audit log and feedback for system improvement.
*   **`PROJECT_STRUCTURE.md`**: (This file) Navigation aid.
*   **`TODO.md`**: Roadmap and change tracking.

## `app/` Directory (Core Logic)

*   **`main.py`**:
    *   **Entry Point**: Initializes the FastAPI application.
    *   **Middleware**: Sets up Prometheus instrumentation.
    *   **Routes**: Includes the API router.
    *   **Health Check**: `/health` endpoint.

*   **`api.py`**:
    *   **Router**: Defines REST endpoints:
        *   `GET /analyze/{ticker}`: Full AI + Quantitative analysis.
        *   `GET /technical/{ticker}`: Raw technicals and algo score.
        *   `GET /fundamentals/{ticker}`: Financial data.
        *   `GET /context/{ticker}`: Market context (analysts, insiders).
    *   **Delegation**: Calls functions in `service.py`.

*   **`service.py`**:
    *   **The Governor**: Implements `STierTradingSystem` class.
    *   **State Machine**: Manages `DecisionState` (ACCEPT, WAIT, REJECT) and `SetupState`.
    *   **Risk Engine**: Enforces `RiskParameters` (0.5% max risk).
    *   **Orchestration**: Combines Technicals, Fundamentals, and Context to produce a `TradingDecision`.
    *   **Data Integrity**: Sanitizes inputs and hard-nulls poisoned indicators.

*   **`models.py`**:
    *   **Schema Definitions**: Pydantic models for all API responses.
    *   **Enums**: `DecisionState`, `DataIntegrity`, `SetupState`, `SetupQuality`, `TradeAction`.
    *   **Type Safety**: Ensures strict data contracts between layers.

*   **`technicals.py`**:
    *   **Math Engine**: Calculates indicators (RSI, MACD, ADX, CCI, Bollinger Bands) using `pandas-ta`.
    *   **Scoring**: Computes the "Algo Signal" (-100 to +100).
    *   **Poison Detection**: Identifies and hard-nulls invalid indicator values (e.g., CCI > 500).

*   **`ai.py`**:
    *   **LLM Interface**: interactions with Google Gemini.
    *   **Prompt Engineering**: Constructs strict, context-aware prompts based on the Governor's state.
    *   **Output Parsing**: Validates and parses the AI's JSON response.

*   **`market_data.py`**:
    *   **Data Access**: Fetches historical price data and company info via `yfinance`.
    *   **Concurrency**: Uses `asyncio` for non-blocking I/O.

*   **`fundamentals.py`**:
    *   **Financials**: Fetches balance sheet, income statement, and valuation metrics.
    *   **Sanity Checks**: Validates data relationships (e.g., EV vs Market Cap).

*   **`context.py`**:
    *   **Smart Money**: Fetches Insider Trading, Analyst Ratings, and Option Sentiment.
    *   **Filtering**: Filters for relevant/material activity (e.g., recent insider sales).

*   **`settings.py`**:
    *   **Configuration**: Manages environment variables (API Keys, Timeouts) via Pydantic Settings.

## Utility Scripts (Root)

*   **`inspect_*.py`**: Standalone scripts for debugging specific data feeds (analysts, news, yfinance).
*   **`debug_context_run.py`**: Script to test the context fetching logic in isolation.
