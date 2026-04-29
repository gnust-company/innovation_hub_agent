"""LangFuse v4 monitoring — CallbackHandler + propagate_attributes."""
import os
from contextlib import contextmanager
from typing import Optional

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from src.utils.logger import logger


def _is_configured() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@contextmanager
def trace_agent_call(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Create CallbackHandler for non-streaming calls. propagate_attributes sets trace-level user/session."""
    if not _is_configured():
        yield _NoopContext()
        return

    handler = CallbackHandler()
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or "",
        trace_name="agent_query",
    ):
        yield _TraceContext(handler=handler)

    get_client().flush()


def start_trace(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Create CallbackHandler for async streaming. propagate_attributes handles trace attrs."""
    if not _is_configured():
        return _NoopContext()
    handler = CallbackHandler()
    return _TraceContext(
        handler=handler,
        user_id=user_id or "",
        session_id=session_id or "",
    )


def end_trace(ctx):
    """Flush Langfuse after streaming completes."""
    if not ctx or not ctx.handler:
        return
    try:
        get_client().flush()
    except Exception as e:
        logger.warning(f"Failed to flush Langfuse: {e}")


class _TraceContext:
    __slots__ = ("handler", "user_id", "session_id")

    def __init__(self, handler, user_id="", session_id=""):
        self.handler = handler
        self.user_id = user_id
        self.session_id = session_id


class _NoopContext:
    handler = None
    user_id = ""
    session_id = ""

    def __getattr__(self, _):
        return None
