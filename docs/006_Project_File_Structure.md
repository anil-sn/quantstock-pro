# Project File Structure & Responsibilities

## 📂 Root Directory
- `pyproject.toml`: Dependency management and build configuration (UV-optimized).
- `README.md`: Project overview and institutional standard guide.
- `STRUCTURE.md`: Map of architectural layers and data flow.

## 📂 app/ (Source Root)
- `main.py`: Entry point; router mounting and global middleware.
- `api_v2.py`: The resource-oriented 2.0 API implementation.
- `models_v2.py`: Enhanced Pydantic schemas for the 2.0 interface.
- `service.py`: Central trading system brain and orchestrator.
- `ai.py`: Gemini narrative engine with schema repair logic.
- `technicals_indicators.py`: Robust technical math with NaN forward-filling.
- `fundamentals_analytics.py`: Intrinsic valuation models (DCF, Graham).
- `logger.py`: Forensic rich-text logging utility.

## 📂 tests/
- `test_api_v2.py`: Verification of versioned REST endpoints.
- `test_real_world_forensics.py`: Live market data audits for US and Intl tickers.
- `test_ai_integration.py`: Validation of structured Gemini synthesis.
- `test_core_logic.py`: Verification of mathematical and rule-based invariants.

## 📂 docs/
- `003_REST_API_Referance.md`: Detailed endpoint definitions for v2.0.
- `004_Code_Structure_and_Functions.md`: Granular functional map.
- `005_System_Design.md`: High-level architectural philosophy.
- `TODO.md`: Roadmap and completed audit trails.