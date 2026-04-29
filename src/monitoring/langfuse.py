"""LangFuse monitoring — CallbackHandler + trace wrapper for LangGraph."""
import os
from contextlib import contextmanager
from typing import Optional

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from src.utils.logger import logger


def _is_configured() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@contextmanager
def trace_agent_call(
    query: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Wrap agent call in Langfuse observation for correct trace-level user/session/name.

    Yields handler to pass into agent.invoke config={"callbacks": [ctx.handler]}.
    Set output on ctx.span before exiting.
    """
    if not _is_configured():
        yield _NoopContext()
        return

    client = Langfuse()
    handler = CallbackHandler()

    with client.start_as_current_observation(
        as_type="span",
        name="agent_query",
        trace_context={
            "trace_id": client.create_trace_id(),
            "user_id": user_id or "",
            "session_id": session_id or "",
        },
    ) as span:
        span.update(input=query)
        yield _TraceContext(handler=handler, span=span)

    client.flush()


class _TraceContext:
    __slots__ = ("handler", "span")

    def __init__(self, handler, span):
        self.handler = handler
        self.span = span


class _NoopContext:
    handler = None
    span = None

    def __getattr__(self, _):
        return None
