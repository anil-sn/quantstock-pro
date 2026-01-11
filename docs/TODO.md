# TODO: Immediate Survival Hotfixes & Architectural Overhaul

## 🚀 API v2.0 Refactoring (Institutional Standard) - COMPLETED ✅
- [x] **Versioning**: Implemented `/api/v2/` hierarchy in `app/api_v2.py`.
- [x] **Resource Orientation**: Decoupled Analysis, Technicals, Fundamentals, and News intelligence.
- [x] **Asynchronous Research**: Implemented `POST /research/{ticker}` for background research tasks.
- [x] **Enhanced Models**: Defined `AnalysisResponse` and `MetaInfo` in `app/models_v2.py`.
- [x] **V1 Removal**: Completely purged the legacy v1.0 interface.

## 🧠 AI Synthesis Optimization (High-Fidelity) - COMPLETED ✅
- [x] **Structured Reporting**: Implemented mandatory Markdown headers and tables in `executive_summary`.
- [x] **Data Enforcement**: Integrated explicit constraints for confidence capping and level consistency.
- [x] **Schema Resilience**: Added markdown stripping, JSON unwrapping, and schema repair for AI model output.
- [x] **Multi-Horizon Data**: Enriched LLM prompt with 4 time-horizons of technical indicators.

## 🛡️ Mathematical Hardening & Forensics - COMPLETED ✅
- [x] **Zero Silent Failures**: Replaced all `except: pass` blocks with granular `pipeline_logger` calls.
- [x] **Math Integrity**: Fixed "Expectancy Leak" and "Zero Division" bugs in scoring and scenarios.
- [x] **NaN Resilience**: Implemented technical indicator forward-filling and numeric-guaranteed CCI.
- [x] **100% Validation**: Every ticker now passes full Pydantic validation across all sensors.

## 🧪 Testing Standard (Highest Grade) - COMPLETED ✅
- [x] **Live Forensics**: Built `tests/test_real_world_forensics.py` for audit-grade ticker verification.
- [x] **Combinatorial API**: Verified 32 permutations of REST endpoints and parameters.
- [x] **Environment Sync**: Locked dependencies in `pyproject.toml` and verified with `uv run`.

## 📈 Roadmap & Enhancements
- [ ] **Brutal Alpha Remediation (Final Polish)**:
    - [x] **Task 1: Event Loop Protection**: Wrap all remaining sync provider calls in `run_in_threadpool`.
    - [x] **Task 2: Accounting Quality Gate**: Implement Sloan Ratio validation to detect earnings manipulation.
    - [x] **Task 3: Signal Logic Tightening**: Upgrade primary signal to a Gated Product model.
    - [ ] **Task 4: Documentation Polish**: Add Mermaid sequence diagrams to System Design.
- [x] **Redis Distributed Caching Integration**:
    - [x] **Infrastructure**: Implement `app/cache.py` with Redis connection pooling and fallback logic.
    - [x] **Market Data Migration**: Port `app/market_data.py` to Redis-backed caching.
    - [ ] **Analytical Migration**: Port `app/fundamentals.py` and scoring modules to Redis.
    - [ ] **AI Narrative Migration**: Port `app/ai.py` prompt-hash caching to Redis.
- [ ] **Streaming Support**: Implement Server-Sent Events (SSE) for real-time signal propagation.
- [ ] **Portfolio Risk**: Add cross-sector correlation and beta-adjusted risk checks.
- [ ] **Monte Carlo Logic**: Move from 3-point trees to full probabilistic distribution models.
- [ ] **Interactive AI**: Add `/api/v2/ai/explain/{signal}` for deep dive narrative queries.

## 2026-01-12: System Analysis and Verification

- [x] Conducted thorough project analysis and functionality mapping.

- [x] Created docs/008_Project_Navigation.md for codebase navigation.

- [x] Run pytest -x and debug first failure.

    - [x] Fixed `ImportError` by correctly setting `PYTHONPATH`.

    - [x] Fixed `AssertionError` in `test_e2e_signal_math_integrity` by ensuring `algo_signal` is always populated in `get_technical_analysis` return paths.

- [x] Verified test quality and model coverage.

    - [x] Implemented `tests/test_response_integrity.py` for 100% field validation of `AnalysisResponse`.

    - [x] Fixed confidence capping bug in `get_technical_analysis`.

- [x] Conducted in-depth full validation of each field using `pytest -x`.

    - [x] Upgraded `test_response_integrity.py` and `test_api_v2.py` for deep nested validation.

    - [x] Synchronized institutional invariants in `test_institutional_invariants.py`.

    - [x] Resolved all subscripting and logic errors across the test suite.

    - [x] 100% Pass Rate (96/96 tests) across the entire system.


