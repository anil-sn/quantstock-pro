# QuantStock-Pro: System Design & Architecture

## 1. Architectural Philosophy
QuantStock-Pro is built on the **PRAR** (Perceive, Reason, Act, Refine) workflow, evolved for institutional-grade reliability. The core design principle is **Execution-First Architecture**, ensuring that high-latency components (like LLMs) never gate critical trading decisions.

## 2. Dual-Engine Execution Model

### 2.1 The Fast Path (Deterministic Engine)
The Fast Path is the system's "reflex." It is responsible for low-latency, rule-based decision making.
*   **Latency Target**: < 500ms.
*   **Mechanism**: Pure Python logic, statistical signals, and a **Veto Registry**.
*   **Authority**: Canonical. It determines if a trade is `authorized`. If the Fast Path issues a `WAIT` or `REJECT` due to a veto (e.g., ADX < 20), the Slow Path is bypassed to save resources and time.

### 2.2 The Slow Path (Narrative Engine)
The Slow Path is the system's "brain." It provides deep synthesis and human-readable context.
*   **Latency Profile**: 10s - 30s.
*   **Mechanism**: Google Gemini Pro (LLM).
*   **Safety**: Gated by a **5-second Circuit Breaker**. If the LLM exceeds 5 seconds, the system returns the deterministic decision with a `fallback_used` flag.
*   **Constraint**: The Slow Path must strictly adhere to the `system.confidence` and `execution.action` defined by the Fast Path.

## 3. Decision Pipeline (Forensic Layers)

1.  **Layer 0: Context (Parallel)**: Fetches "Smart Money" data (Insiders, Options) and Market Events.
2.  **Layer 1: Sensors (Parallel)**: Multi-horizon technical analysis (Intraday to Longterm) and Fundamental scoring.
3.  **Layer 2: Alpha Expectancy**: Calculates the probabilistic edge (P_Win) and EV. Wired directly into the primary signal strength.
4.  **Layer 3: Synthesis**: Optional LLM-based interpretation (Gated by Stage 1 results).
5.  **Layer 4: Audit/Audit**: Final invariant enforcement (e.g., Confidence Clamping, R:R validation).

## 4. Institutional Governance Invariants

### 4.1 Single Source of Truth (SSoT)
*   Exactly **one confidence scalar** (`system.confidence`) is authoritative for the entire report.
*   The `execution.action` block is the sole source of instruction for trading platforms.

### 4.2 Data Absence Taxonomy
Instead of generic "Sensor Failures," the system uses a granular taxonomy:
*   `DATA_ABSENT`: Source returned no data (expected for some tickers).
*   `CALCULATION_FAILURE`: Math could not be completed.
*   `STALE_DATA`: Data exists but exceeds freshness thresholds.

### 4.3 Veto Registry
Every `WAIT` or `REJECT` decision must be justified in the `execution.vetoes` list. Common vetoes include:
*   `REGIME_VALUATION_CONFLICT`: High price vs target + Low trend.
*   `LIQUIDITY_INSUFFICIENT`: Volume below institutional thresholds.
*   `DATA_INTEGRITY_REJECTED`: Contradictory signals (e.g., Positive NI with Negative ROE).

## 5. Risk & Math Integrity
*   **Signal Normalization**: All components (Trend, Momentum, etc.) are normalized to a strict `[-1, 1]` range.
*   **Weighted Aggregation**: `primary_signal_strength = Σ(weight_i * score_i)`. Math is transparent and verifiable in the `signals` block.
*   **Dynamic Risk**: `max_capital_risk_pct` is dynamically scaled based on `ATR_pct` to ensure stop-losses survive normal market noise.

## 6. Telemetry & Monitoring
The system provides millisecond-level timings for every layer (`l0_context`, `l1_sensors`, `l3_synthesis`) and flags `latency_sla_violated` if the total cycle exceeds 5 seconds.
