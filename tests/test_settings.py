import os
import pytest
from app.settings import Settings

def test_settings_default_values(monkeypatch):
    """Verify that default settings are loaded correctly."""
    monkeypatch.setenv("QUANTSTOCK_GEMINI_API_KEY", "dummy_key")
    settings = Settings(_env_file=None) # Don't load actual .env
    assert settings.APP_NAME == "QuantStock Pro API"
    assert settings.ENVIRONMENT == "development"

def test_settings_env_override(monkeypatch):
    """Verify that environment variables override defaults."""
    monkeypatch.setenv("QUANTSTOCK_GEMINI_API_KEY", "dummy_key")
    monkeypatch.setenv("QUANTSTOCK_APP_NAME", "Test Override")
    monkeypatch.setenv("QUANTSTOCK_ENVIRONMENT", "production")
    
    settings = Settings(_env_file=None)
    assert settings.APP_NAME == "Test Override"
    assert settings.ENVIRONMENT == "production"

def test_settings_risk_parameters(monkeypatch):
    """Verify risk parameter defaults."""
    monkeypatch.setenv("QUANTSTOCK_GEMINI_API_KEY", "dummy_key")
    settings = Settings(_env_file=None)
    assert settings.MAX_POSITION_PCT == 5.0
    assert settings.CONFIDENCE_THRESHOLD == 70.0
