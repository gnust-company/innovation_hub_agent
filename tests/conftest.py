"""Shared test fixtures."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient


TEST_API_KEY = "test-agent-key-12345"


@pytest.fixture
def tmp_wiki(tmp_path):
    """Create a minimal wiki vault for testing."""
    index = tmp_path / "00_Index"
    index.mkdir()
    (index / "Welcome.md").write_text("# Welcome\nHello world [[Getting_Started]]")
    (tmp_path / "Getting_Started.md").write_text("# Getting Started\nSome content")
    return str(tmp_path)


@pytest.fixture
def app_client(tmp_wiki, monkeypatch):
    """FastAPI TestClient with mocked env vars — agent NOT initialized (no LLM key)."""
    monkeypatch.setenv("AGENT_API_KEY", TEST_API_KEY)
    monkeypatch.setenv("WIKI_PATH", tmp_wiki)
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    monkeypatch.setenv("AGENT_ENV", "test")

    from src.api.app import app
    # Simulate lifespan: set config manually (skip LLM init)
    from src.agent.config import AgentConfig
    app.state.config = AgentConfig()
    app.state.agent = None  # No real agent in tests

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid API key."""
    return {"X-API-Key": TEST_API_KEY}
