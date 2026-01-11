# TODO: Immediate Survival Hotfixes & Architectural Overhaul

## 🚀 API v2.0 Refactoring (Institutional Standard) - COMPLETED ✅
- [x] **Versioning**: Implemented `/api/v2/` hierarchy in `app/api_v2.py`.
- [x] **Resource Orientation**: Decoupled Analysis, Technicals, Fundamentals, and News intelligence.
- [x] **Asynchronous Research**: Implemented `POST /research/{ticker}` for background research tasks.
- [x] **Enhanced Models**: Defined `AnalysisResponse` and `MetaInfo` in `app/models_v2.py`.
- [x] **Backward Compatibility**: Preserved v1.0 interface alongside the new v2.0 core.

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
- [ ] **Streaming Support**: Implement Server-Sent Events (SSE) for real-time signal propagation.
- [ ] **Portfolio Risk**: Add cross-sector correlation and beta-adjusted risk checks.
- [ ] **Monte Carlo Logic**: Move from 3-point trees to full probabilistic distribution models.
- [ ] **Interactive AI**: Add `/api/v2/ai/explain/{signal}` for deep dive narrative queries.