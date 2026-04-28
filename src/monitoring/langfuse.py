"""LangFuse v4 monitoring — optional, graceful when not configured."""
import os
import re
from typing import Optional

from langfuse import Langfuse

from src.utils.logger import logger

_client: Langfuse | None = None
_initialized: bool = False

# Sentence boundary: flush buffer on these endings
_SENTENCE_END = re.compile(r'[.!?。\n]\s*$')


def get_langfuse() -> Langfuse | None:
    """Get singleton Langfuse client. Returns None if not configured."""
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    if not pk or not sk:
        logger.info("LangFuse not configured (missing LANGFUSE_PUBLIC_KEY/SECRET_KEY)")
        return None

    try:
        _client = Langfuse(
            public_key=pk,
            secret_key=sk,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        logger.info("LangFuse client initialized")
        return _client
    except Exception as e:
        logger.warning(f"LangFuse init failed: {e}")
        return None


def flush():
    """Flush pending Langfuse events."""
    if _client:
        _client.flush()


def shutdown():
    """Shutdown Langfuse client gracefully."""
    global _client, _initialized
    if _client:
        _client.shutdown()
        _client = None
        _initialized = False


class AgentTrace:
    """Tracks one agent query as a Langfuse trace with aggregated logging.

    Buffers streaming "thinking" chunks and flushes them as complete
    sentences/spans instead of per-token.
    """

    def __init__(self, query: str, thread_id: str,
                 user_id: str = "", username: str = "", role: str = ""):
        self.client = get_langfuse()
        self.trace = None
        self._thinking_buf: list[str] = []
        self._thinking_span = None
        self._tool_span = None
        self._generation_span = None

        if not self.client:
            return

        try:
            self.trace = self.client.trace(
                name="agent_query",
                input=query,
                session_id=thread_id or None,
                user_id=username or None,
                metadata={
                    "thread_id": thread_id,
                    "username": username,
                    "user_id": user_id,
                    "role": role,
                },
            )
        except Exception as e:
            logger.warning(f"Langfuse trace creation failed: {e}")

    @property
    def active(self) -> bool:
        return self.trace is not None

    # --- Thinking (LLM output) ---

    def on_thinking_chunk(self, content: str):
        """Buffer a thinking chunk. Flushes on sentence boundary."""
        if not self.active:
            return
        self._thinking_buf.append(content)
        full = "".join(self._thinking_buf)
        if _SENTENCE_END.search(full.rstrip()) or len(full) > 500:
            self._flush_thinking(full)
            self._thinking_buf = []

    def _flush_thinking(self, text: str):
        """Log a complete thinking block as a generation span."""
        if not text.strip():
            return
        try:
            if self._thinking_span:
                self._thinking_span.end(output=text)
            self._thinking_span = self.trace.generation(
                name="reasoning",
                output=text,
            )
        except Exception as e:
            logger.debug(f"Langfuse thinking log failed: {e}")

    def flush_thinking(self):
        """Flush any remaining buffered thinking."""
        if self._thinking_buf:
            self._flush_thinking("".join(self._thinking_buf))
            self._thinking_buf = []
        self._thinking_span = None

    # --- Tool calls ---

    def on_tool_start(self, name: str, args: dict):
        """Start a tool span."""
        if not self.active:
            return
        self.flush_thinking()  # flush any pending thinking before tool
        try:
            self._tool_span = self.trace.span(
                name=f"tool:{name}",
                input=args,
                metadata={"tool": name},
            )
        except Exception as e:
            logger.debug(f"Langfuse tool start failed: {e}")

    def on_tool_end(self, output: str):
        """End current tool span with result."""
        if not self.active or not self._tool_span:
            return
        try:
            self._tool_span.end(output=output[:2000])
        except Exception as e:
            logger.debug(f"Langfuse tool end failed: {e}")
        self._tool_span = None

    # --- Final answer ---

    def on_complete(self, answer: str, sources: list[str],
                    token_usage: dict | None = None):
        """Log final answer and close trace."""
        if not self.active:
            return
        self.flush_thinking()
        try:
            metadata = {"sources": sources}
            if token_usage:
                metadata["token_usage"] = token_usage
            self.trace.update(
                output=answer,
                metadata=metadata,
            )
        except Exception as e:
            logger.debug(f"Langfuse trace complete failed: {e}")

    def on_error(self, error: str):
        """Log error on trace."""
        if not self.active:
            return
        try:
            self.trace.update(metadata={"error": error})
        except Exception:
            pass
