import pytest
import os

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "live: mark test as making live API calls (Yahoo, NewsAPI)",
    )
    config.addinivalue_line(
        "markers",
        "requires_llm: mark test as requiring a real LLM (Gemini)",
    )

@pytest.fixture(scope="session")
def check_api_keys():
    """Verify that required API keys are present for live tests."""
    missing = []
    if not os.getenv("QUANTSTOCK_GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")
    return missing
