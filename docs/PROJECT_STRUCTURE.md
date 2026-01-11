# Project Structure

## Architecture Overview
The system follows a strict **"Perceive-Reason-Act"** architecture, split into two execution speeds to handle LLM latency.

### 1. Data Ingestion (Perceive)
*   **Context Layer**: Insiders, Options, Analyst Targets.
*   **Sensor Layer**: OHLCV data, Financial Statements, News Feeds.
*   **Research Layer**: Deep web search iterations for fundamental grounding.

### 2. Analytical Core (Reason)
*   **Technicals Module**: Calculates multi-horizon indicators and trend structure.
*   **Fundamentals Module**: Quantitative business quality scoring and Intrinsic Valuation (DCF).
*   **News Intelligence**: Noise/Signal classification.
*   **Alpha Expectancy (L2)**: Bayesian P_Win estimation and EV calculation.

### 3. Governance & Authority (Refine)
*   **Signal Governor**: Applies trading rules (Vetoes).
*   **Confidence Ceiling**: Clamps sub-module confidence to the global system limit.
*   **Single Source of Truth**: Enforces consistent scalars across human and machine payloads.

### 4. Execution Logic (Act)
*   **Fast Path**: Deterministic rule engine issuing decisions in <500ms.
*   **Slow Path**: AI synthesis for executive summaries and scenarios (async/optional).
*   **Trade Executor**: Level calculation (Stop-loss, Entry zones).

## Directory Map
*   `app/`: Primary source code.
    *   `research/`: Deep research agent logic.
*   `docs/`: Comprehensive system documentation.
*   `tests/`: Suite of 20+ tests for API, Logic, and Invariants.
*   `logs/`: Forensic pipeline logs for audit trails.
