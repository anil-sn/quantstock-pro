# QuantStock-Pro: System Design & Architecture

## 1. Architectural Philosophy
Built on the **PRAR** (Perceive, Reason, Act, Refine) workflow, evolved for institutional-grade reliability. The core design principle is **Execution-First Architecture**, ensuring high-latency AI synthesis never gates critical trading decisions.

## 2. Decision Pipeline (Forensic Layers)

1.  **Layer 0: Pre-Screen (Governance)**: Immediate filtering based on earnings proximity, insider activity, and data integrity.
2.  **Layer 1: Sensors (Ingestion)**: Multi-horizon technical OHLCV and detailed financial statements from Polygon/Yahoo.
3.  **Layer 2: Scoring (Quantitative Edge)**: 
    - **Bayesian Engine**: Calculates P_Win based on regime-aware technical indicators.
    - **Quality Engine**: DCF and sector-relative fundamental grading.
4.  **Layer 3: Synthesis (Intelligence)**: Gemini LLM generates evidentiary reports in Markdown format.
5.  **Layer 4: Enforcement (Audit)**: Mandatory confidence capping and price-level alignment (Instruction 8, 9, 10).

## 3. API v2.0 Architecture
The system employs a RESTful resource hierarchy under the `/api/v2/` namespace. 
- **Deterministic Fast Path**: Rule-based results in <500ms.
- **AI-Hybrid Slow Path**: Evidentiary synthesis in 10-30s.

## 4. Institutional Guardrails
- **Confidence Ceiling**: Sub-horizon confidence cannot exceed the global system-assessed confidence.
- **Zero Silent Failures**: Every sensor exception is logged and reported via the `data_state_taxonomy`.
- **Mathematical Integrity**: Normalized signal components [-1, 1] across all scoring modules.