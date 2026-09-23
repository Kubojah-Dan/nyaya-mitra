"""
Tests for NyayaMitra Meta Models and System Inspection Router
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_meta_models_endpoint_success():
    """Verify GET /api/v1/meta/models returns all 3 tiers and active primary/fallback models without secrets."""
    response = client.get("/api/v1/meta/models")
    assert response.status_code == 200
    data = response.json()

    assert "tiers" in data
    assert "FAST" in data["tiers"]
    assert "BALANCED" in data["tiers"]
    assert "REASONING" in data["tiers"]

    fast = data["tiers"]["FAST"]
    assert fast["primary_model"] == "gemini-2.0-flash"
    assert fast["fallback_model"] == "llama3-70b-8192"

    balanced = data["tiers"]["BALANCED"]
    assert balanced["primary_model"] == "gemini-2.0-pro"
    assert balanced["fallback_model"] == "llama3-70b-8192"

    reasoning = data["tiers"]["REASONING"]
    assert reasoning["primary_model"] == "gemini-1.5-pro"
    assert reasoning["fallback_model"] == "mixtral-8x7b-32768"

    # Ensure no API keys or secrets are leaked
    raw_text = response.text.lower()
    assert "api_key" not in raw_text
    assert "secret" not in raw_text
    assert "password" not in raw_text


def test_meta_system_endpoint_success():
    """Verify GET /api/v1/meta/system lists all core challenge modules."""
    response = client.get("/api/v1/meta/system")
    assert response.status_code == 200
    data = response.json()

    assert "NyayaMitra" in data["app_name"]
    module_verbs = [m["verb"] for m in data["modules"]]
    assert "understand" in module_verbs
    assert "compare" in module_verbs
    assert "navigate" in module_verbs
