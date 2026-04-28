"""Agent configuration — safety limits, timeouts, and model settings."""
import os
from dataclasses import dataclass, field


def _env(key: str, type_: type, default):
    """Read env var with type casting."""
    raw = os.getenv(key)
    if raw is None:
        return default
    return type_(raw)


@dataclass
class AgentConfig:
    """Agent configuration with env var overrides."""

    # Safety limits
    max_tool_calls: int = field(default_factory=lambda: _env("MAX_TOOL_CALLS", int, 10))
    max_tokens: int = field(default_factory=lambda: _env("MAX_TOKENS", int, 4096))
    tool_timeout_seconds: int = field(default_factory=lambda: _env("TOOL_TIMEOUT_SECONDS", int, 30))

    # LLM
    llm_max_retries: int = field(default_factory=lambda: _env("LLM_MAX_RETRIES", int, 3))
    model_name: str = field(default_factory=lambda: _env("MODEL_NAME", str, "moonshotai/kimi-k2.5"))
    base_url: str = field(default_factory=lambda: _env("NVIDIA_BASE_URL", str, "https://integrate.api.nvidia.com/v1"))
    temperature: float = field(default_factory=lambda: _env("TEMPERATURE", float, 0.0))
