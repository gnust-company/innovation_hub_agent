"""Shared test fixtures."""
import pytest
from fastapi.testclient import TestClient


TEST_API_KEY = "test-agent-key-12345"
TEST_LLM_KEY = "test-llm-key-fake"


@pytest.fixture
def app_client(monkeypatch):
    """FastAPI TestClient with mocked env vars — agent NOT initialized (no LLM key)."""
    monkeypatch.setenv("AGENT_API_KEY", TEST_API_KEY)
    monkeypatch.setenv("MCP_URL", "http://localhost:9999")
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    monkeypatch.setenv("AGENT_ENV", "test")

    from src.api.app import app
    from src.agent.config import AgentConfig

    app.state.config = AgentConfig()

    # Mock MCP tools as loaded (so /ready passes)
    import src.agent.core as core
    core._mcp_tools = [type("FakeTool", (), {"name": "fake_tool"})()]
    core._system_prompt = "test system prompt"

    yield TestClient(app)

    core._mcp_tools = []
    core._system_prompt = ""


@pytest.fixture
def auth_headers():
    """Headers with valid API key and LLM key."""
    return {"X-API-Key": TEST_API_KEY, "X-LLM-API-Key": TEST_LLM_KEY}
