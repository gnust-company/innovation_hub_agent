"""Tests for LangFuse monitoring module."""
import os
import pytest
from unittest.mock import MagicMock, patch, call

from src.monitoring.langfuse import AgentTrace, _SENTENCE_END


class TestSentenceBoundaryDetection:
    def test_period_ends_sentence(self):
        assert _SENTENCE_END.search("Hello world.")

    def test_question_mark_ends_sentence(self):
        assert _SENTENCE_END.search("How are you?")

    def test_exclamation_ends_sentence(self):
        assert _SENTENCE_END.search("Great!")

    def test_newline_ends_sentence(self):
        assert _SENTENCE_END.search("line one\n")

    def test_no_boundary_mid_sentence(self):
        assert _SENTENCE_END.search("Hello world") is None

    def test_vietnamese_period(self):
        assert _SENTENCE_END.search("Xin chào.")


class TestAgentTraceWithoutLangfuse:
    """AgentTrace should be a no-op when Langfuse is not configured."""

    def test_no_env_vars_graceful(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove langfuse keys if present
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            # Reset module state
            import src.monitoring.langfuse as lf_mod
            lf_mod._client = None
            lf_mod._initialized = False

            trace = AgentTrace(query="test", thread_id="t1")
            assert not trace.active

            # All methods should be no-ops
            trace.on_thinking_chunk("Hello ")
            trace.on_thinking_chunk("world.")
            trace.on_tool_start("read_file", {"path": "test.md"})
            trace.on_tool_end("content")
            trace.on_complete("answer", ["test.md"])
            trace.on_error("oops")


class TestAgentTraceWithMock:
    """Test AgentTrace with mocked Langfuse client."""

    @pytest.fixture
    def mock_langfuse(self):
        mock_client = MagicMock()
        mock_trace = MagicMock()
        mock_client.trace.return_value = mock_trace

        import src.monitoring.langfuse as lf_mod
        lf_mod._client = mock_client
        lf_mod._initialized = True

        yield mock_client, mock_trace

        lf_mod._client = None
        lf_mod._initialized = False

    def test_creates_trace_with_metadata(self, mock_langfuse):
        mock_client, mock_trace = mock_langfuse

        trace = AgentTrace(
            query="Innovation Hub là gì?",
            thread_id="thread-123",
            user_id="uid-456",
            username="admin",
            role="admin",
        )

        assert trace.active
        mock_client.trace.assert_called_once_with(
            name="agent_query",
            input="Innovation Hub là gì?",
            session_id="thread-123",
            user_id="admin",
            metadata={
                "thread_id": "thread-123",
                "username": "admin",
                "user_id": "uid-456",
                "role": "admin",
            },
        )

    def test_thinking_chunks_aggregated(self, mock_langfuse):
        _, mock_trace = mock_langfuse

        trace = AgentTrace(query="test", thread_id="t1")

        # Send chunks that don't form a sentence yet
        trace.on_thinking_chunk("Hello ")
        trace.on_thinking_chunk("world")
        # No generation logged yet (not a complete sentence)
        mock_trace.generation.assert_not_called()

        # Send final chunk with period
        trace.on_thinking_chunk(".")
        # Now should flush
        assert mock_trace.generation.call_count >= 1

    def test_tool_lifecycle(self, mock_langfuse):
        _, mock_trace = mock_langfuse

        trace = AgentTrace(query="test", thread_id="t1")

        mock_span = MagicMock()
        mock_trace.span.return_value = mock_span

        trace.on_tool_start("read_file", {"path": "00_Index/MOC_Overview.md"})
        mock_trace.span.assert_called_with(
            name="tool:read_file",
            input={"path": "00_Index/MOC_Overview.md"},
            metadata={"tool": "read_file"},
        )

        trace.on_tool_end("Innovation Hub overview content...")
        mock_span.end.assert_called_once_with(output="Innovation Hub overview content...")

    def test_on_complete_logs_answer_and_sources(self, mock_langfuse):
        _, mock_trace = mock_langfuse

        trace = AgentTrace(query="test", thread_id="t1")
        trace.on_complete(
            answer="Innovation Hub là nền tảng.",
            sources=["00_Index/MOC_Overview.md"],
            token_usage={"prompt_tokens": 50, "completion_tokens": 100},
        )

        mock_trace.update.assert_called_once_with(
            output="Innovation Hub là nền tảng.",
            metadata={
                "sources": ["00_Index/MOC_Overview.md"],
                "token_usage": {"prompt_tokens": 50, "completion_tokens": 100},
            },
        )

    def test_on_error(self, mock_langfuse):
        _, mock_trace = mock_langfuse

        trace = AgentTrace(query="test", thread_id="t1")
        trace.on_error("LLM timeout")

        mock_trace.update.assert_called_with(metadata={"error": "LLM timeout"})

    def test_flush_thinking_on_tool_start(self, mock_langfuse):
        """Thinking buffer should flush before a tool call."""
        _, mock_trace = mock_langfuse

        trace = AgentTrace(query="test", thread_id="t1")

        trace.on_thinking_chunk("Thinking about this. ")
        trace.on_tool_start("read_file", {"path": "test.md"})

        # Generation should be called for the thinking that was flushed
        mock_trace.generation.assert_called()


class TestGetLangfuse:
    def test_returns_none_without_env(self):
        import src.monitoring.langfuse as lf_mod
        lf_mod._client = None
        lf_mod._initialized = False

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            result = lf_mod.get_langfuse()
            assert result is None

    def test_returns_client_with_env(self):
        import src.monitoring.langfuse as lf_mod
        lf_mod._client = None
        lf_mod._initialized = False

        with patch.dict(os.environ, {
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
        }):
            with patch("src.monitoring.langfuse.Langfuse") as mock_lf:
                mock_instance = MagicMock()
                mock_lf.return_value = mock_instance

                result = lf_mod.get_langfuse()
                assert result is mock_instance
                mock_lf.assert_called_once()
