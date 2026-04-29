"""Structured logging for agent runs."""
import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

logger = logging.getLogger("innovation_hub_agent")


def setup_logging(level: str = "INFO"):
    """Configure structured logging."""
    if logger.handlers:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))


@dataclass
class RunTrace:
    """Captures one agent run for structured logging."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    query: str = ""
    tools_called: list = field(default_factory=list)
    files_read: list = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)
    start_time: float = 0.0
    duration_seconds: float = 0.0
    error: str = ""

    def record_tool(self, name: str, args: dict):
        self.tools_called.append(name)
        if name == "read_file":
            self.files_read.append(args.get("path", ""))

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "query": self.query[:200],
            "tools_called": self.tools_called,
            "files_read": self.files_read,
            "token_usage": self.token_usage,
            "duration_seconds": round(self.duration_seconds, 2),
            "error": self.error,
        }


@contextmanager
def trace_run(query: str):
    """Context manager to trace an agent run."""
    trace = RunTrace(query=query, start_time=time.time())
    logger.info(f"[{trace.run_id}] START query={query[:100]}")
    try:
        yield trace
    except Exception as e:
        trace.error = str(e)
        logger.error(f"[{trace.run_id}] ERROR: {e}")
        raise
    finally:
        trace.duration_seconds = time.time() - trace.start_time
        logger.info(f"[{trace.run_id}] DONE tools={trace.tools_called} "
                     f"files={len(trace.files_read)} "
                     f"duration={trace.duration_seconds:.2f}s "
                     f"tokens={trace.token_usage}")
