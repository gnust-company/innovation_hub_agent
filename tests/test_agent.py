"""Integration tests for the full agent flow."""
import os
import pytest

from src.agent.config import AgentConfig
from src.agent.core import create_agent, run_query


@pytest.fixture
def agent(tmp_wiki, monkeypatch):
    """Create agent pointing at tmp_wiki."""
    monkeypatch.setenv("WIKI_PATH", str(tmp_wiki))
    monkeypatch.setenv("NVIDIA_API_KEY", os.getenv("NVIDIA_API_KEY", "test"))
    # Skip actual LLM call in CI — only run when API key is valid
    if not os.getenv("NVIDIA_API_KEY"):
        pytest.skip("NVIDIA_API_KEY not set, skipping integration test")

    config = AgentConfig()
    config.max_tool_calls = 5
    agent, config = create_agent(config)
    return agent, config


@pytest.mark.skipif(not os.getenv("NVIDIA_API_KEY"), reason="No API key")
class TestAgentIntegration:
    def test_simple_query(self, agent):
        agent, config = agent
        output = run_query(agent, "Innovation Hub là gì?", "test-integration", config)
        result = output["result"]
        trace = output["trace"]

        # Should have at least one AI message with content
        ai_messages = [m for m in result["messages"] if m.type == "ai" and m.content]
        assert len(ai_messages) >= 1

        # Trace should be populated
        assert trace.query == "Innovation Hub là gì?"
        assert trace.duration_seconds > 0

    def test_tool_calling_query(self, agent):
        agent, config = agent
        output = run_query(agent, "Getting Started guide?", "test-tools", config)
        trace = output["trace"]

        # Should have called read_file at least
        assert "read_file" in trace.tools_called
        assert len(trace.files_read) >= 1

    def test_multi_turn(self, agent):
        agent, config = agent
        thread = "test-multi-turn"

        # First turn
        output1 = run_query(agent, "Có những tính năng gì?", thread, config)
        assert any(m.type == "ai" and m.content for m in output1["result"]["messages"])

        # Second turn (same thread)
        output2 = run_query(agent, "Kể thêm chi tiết về Problem Feed", thread, config)
        ai_msgs = [m for m in output2["result"]["messages"] if m.type == "ai" and m.content]
        assert len(ai_msgs) >= 1
