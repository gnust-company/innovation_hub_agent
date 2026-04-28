"""Tests for the REST API endpoints."""
import json
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def mock_agent():
    """Create a mock agent that returns a simple response."""
    agent = MagicMock()

    ai_msg = MagicMock()
    ai_msg.type = "ai"
    ai_msg.content = "Innovation Hub là nền tảng đổi mới sáng tạo."
    ai_msg.tool_calls = []
    ai_msg.response_metadata = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 20}}

    agent.invoke.return_value = {"messages": [ai_msg]}
    return agent


@pytest.fixture
def mock_config():
    """Create a mock config."""
    from src.agent.config import AgentConfig
    return AgentConfig(
        max_tool_calls=5,
        max_tokens=1024,
        model_name="test-model",
    )


@pytest.fixture
def client(mock_agent, mock_config):
    """Create a test client with mocked agent."""
    os.environ.setdefault("WIKI_PATH", "/tmp/test_wiki")
    os.environ.setdefault("NVIDIA_API_KEY", "test-key")

    with patch("src.api.app.create_agent", return_value=(mock_agent, mock_config)):
        from src.api.app import app
        with TestClient(app) as c:
            yield c


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["model"] == "test-model"


class TestChat:
    def test_chat_returns_answer(self, client, mock_agent):
        resp = client.post("/api/chat", json={
            "message": "Innovation Hub là gì?",
            "thread_id": "test-thread-1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Innovation Hub" in data["answer"]
        assert data["thread_id"] == "test-thread-1"
        assert isinstance(data["sources"], list)

    def test_chat_generates_thread_id(self, client, mock_agent):
        resp = client.post("/api/chat", json={"message": "Hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["thread_id"] != ""

    def test_chat_empty_message_rejected(self, client):
        resp = client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 422

    def test_chat_with_user_metadata(self, client, mock_agent):
        resp = client.post("/api/chat", json={
            "message": "Hello",
            "user_metadata": {"user_id": "123", "username": "admin", "role": "admin"},
        })
        assert resp.status_code == 200

    def test_chat_extracts_sources(self, client, mock_agent):
        # Simulate a tool call in messages
        tool_msg = MagicMock()
        tool_msg.type = "tool"
        tool_msg.content = "file content"

        ai_msg_with_tool = MagicMock()
        ai_msg_with_tool.type = "ai"
        ai_msg_with_tool.content = ""
        ai_msg_with_tool.tool_calls = [{"name": "read_file", "args": {"path": "00_Index/MOC_Overview.md"}}]
        ai_msg_with_tool.response_metadata = {}

        ai_msg_final = MagicMock()
        ai_msg_final.type = "ai"
        ai_msg_final.content = "Overview found."
        ai_msg_final.tool_calls = []
        ai_msg_final.response_metadata = {"token_usage": {}}

        mock_agent.invoke.return_value = {
            "messages": [ai_msg_with_tool, tool_msg, ai_msg_final]
        }

        resp = client.post("/api/chat", json={"message": "Overview?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "00_Index/MOC_Overview.md" in data["sources"]


class TestChatStream:
    def test_stream_returns_events(self, client, mock_agent):
        async def mock_stream(*args, **kwargs):
            chunk1 = MagicMock()
            chunk1.content = "Hello "
            yield {"event": "on_chat_model_stream", "data": {"chunk": chunk1}}

            chunk2 = MagicMock()
            chunk2.content = "world"
            yield {"event": "on_chat_model_stream", "data": {"chunk": chunk2}}

            yield {"event": "on_tool_start", "data": {"name": "read_file", "input": {"path": "test.md"}}}
            output = MagicMock()
            output.content = "file content"
            yield {"event": "on_tool_end", "data": {"output": output}}

        mock_agent.astream_events = mock_stream

        resp = client.post("/api/chat/stream", json={
            "message": "Test",
            "thread_id": "stream-1",
        })
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        # Parse SSE events
        events = []
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        types = [e["type"] for e in events]
        assert "token" in types
        assert "sources" in types
        assert "done" in types
