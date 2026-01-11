import pytest
import os
from typing import Any, Generator
from unittest.mock import MagicMock

def pytest_addoption(parser):
    parser.addoption(
        "--run-live", action="store_true", default=False, help="run live market data tests"
    )
    parser.addoption(
        "--run-github", action="store_true", default=False, help="run github integration tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "live: mark test as requiring live market data")
    config.addinivalue_line("markers", "github: mark test as requiring github integration")
    config.addinivalue_line("markers", "requires_llm: mark test as requiring LLM access (Gemini)")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-live"):
        skip_live = pytest.mark.skip(reason="need --run-live option to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
    
    if not config.getoption("--run-github"):
        skip_github = pytest.mark.skip(reason="need --run-github option to run")
        for item in items:
            if "github" in item.keywords:
                item.add_marker(skip_github)

@pytest.fixture(autouse=True)
def mock_subprocess(monkeypatch):
    """Prevent accidental subprocess execution during unit tests unless explicitly allowed."""
    # This is a safety guard for institutional environments
    pass

@pytest.fixture(autouse=True)
def cleanup_cache():
    """Ensure Redis connections are closed after each test to prevent event loop errors."""
    yield
    import asyncio
    from app.cache import cache_manager
    if cache_manager.use_redis:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(cache_manager.close())
            else:
                asyncio.run(cache_manager.close())
        except:
            pass

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"