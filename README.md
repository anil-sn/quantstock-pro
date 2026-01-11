# QuantStock Pro 🚀

**Institutional-Grade AI Trading Analysis Platform (AlphaCore v20.2)**

QuantStock Pro is a high-performance, modular trading analysis system designed to bridge the gap between retail tools and institutional algorithms. It features a unique **Dual-Engine Architecture** that separates high-speed deterministic execution from deep AI-synthesized narrative research.

---

## 🌟 Key Features

*   **⚡ Dual-Engine Execution**:
    *   **Fast Path**: Deterministic rule engine issuing `WAIT/BUY/SELL` decisions in **<500ms**.
    *   **Slow Path**: AI-powered narrative synthesis (Gemini Pro) for deep investment memos and probability-weighted scenarios.
*   **⚖️ Institutional Governance**: Strict "Signal Governor" enforcing a **Single Source of Truth** for confidence and canonical **Veto Registry**.
*   **🌍 Multi-Horizon Technicals**: Parallel analysis of Intraday, Swing, Positional, and Long-term timeframes.
*   **🔬 Deep Research Agent**: Autonomous Fact-Finding agent that verifies SEC filings and evidentiary data through iterative web searches.
*   **📰 News Intelligence**: Advanced noise filtration that distinguishes "Institutional Signals" from "Retail Hype".
*   **🛡️ Risk & Math Integrity**: Normalized signals [-1, 1], dynamic volatility-adjusted stops, and Bayesian Alpha Expectancy (Layer 2) integration.

---

## 🛠️ Installation

### Prerequisites
*   **Python 3.12**
*   **uv** (Recommended) or `pip`

### Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd quantstock-pro
    ```

2.  **Set up Virtual Environment & Dependencies**
    ```bash
    # Using uv (High Performance)
    uv venv
    source .venv/bin/activate
    uv sync
    ```

3.  **Environment Configuration**
    ```bash
    cp .env_example .env
    ```
    **Required Variables**:
    *   `GEMINI_API_KEY`: For AI synthesis.
    *   `API_KEY`: Secret key for securing endpoints.
    *   `NEWS_API_KEY`: (Optional) For advanced news intelligence.

---

## 🚀 Usage

### Running the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Consumption Patterns

**High-Speed Execution (Deterministic Only)**
*Bypasses the 30s LLM delay for millisecond-level trading orders.*
```bash
curl -X GET "http://localhost:8000/analyze/AAPL?mode=execution" \
     -H "X-API-Key: YOUR_SECRET_KEY"
```

**Full Research (Hybrid Engine)**
*Generates the complete AI investment memo and scenario analysis.*
```bash
curl -X GET "http://localhost:8000/analyze/AAPL?mode=all" \
     -H "X-API-Key: YOUR_SECRET_KEY"
```

---

## 🏗️ Architecture Overview

The system follows a strict **Perceive-Reason-Act** forensic pipeline:

1.  **Layer 0 (Context)**: Parallel ingestion of Insiders, Options, and analyst targets.
2.  **Layer 1 (Sensors)**: Multi-horizon technical indicators and fundamental scoring.
3.  **Layer 2 (Alpha)**: Bayesian P_Win calculation and Expectancy (EV) wiring.
4.  **Layer 3 (Brain)**: Optional AI synthesis with a **5-second Circuit Breaker**.
5.  **Layer 4 (Audit)**: Enforcement of single-scalar confidence and R:R invariants.

See **[docs/DESIGN.md](docs/DESIGN.md)** for the full technical specification.

---

## 🧪 Testing & Validation

We maintain absolute sanity through a multi-tier test suite:

```bash
# Run all tests (API, Core Logic, Institutional Invariants)
uv run pytest
```

*   **API Tests**: Endpoint availability and JSON schema validation.
*   **Core Logic**: Math validation for DCF, Graham Number, and Scoring.
*   **Institutional Invariants**: Rules for Confidence Singularity and WAIT-state safety.

---

## 📚 Detailed Documentation

*   **[API Reference](docs/API_REFERENCE.md)**: Parameters and Response models.
*   **[System Design](docs/DESIGN.md)**: Fast Path/Slow Path architecture.
*   **[File Map](docs/FILE_MAP.md)**: Codebase navigation guide.
*   **[Trading Framework](docs/THE_COMPLETE_FRAMEWORK.md)**: Strategic constitution and veto rules.