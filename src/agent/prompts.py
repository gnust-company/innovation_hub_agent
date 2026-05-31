"""System prompt loader — reads from local file or env var override."""
import os
from pathlib import Path

from src.utils.logger import logger

_PROMPT_FILE = Path(__file__).parent / "system_prompt.md"

_FALLBACK = (
    "You are the Innovation Hub AI Agent. "
    "Use available tools to help users with the Innovation Hub platform."
)


def load_system_prompt() -> str:
    """Load system prompt: env var override -> local file -> hardcoded fallback."""
    env_prompt = os.getenv("SYSTEM_PROMPT", "")
    if env_prompt:
        logger.info("System prompt loaded from SYSTEM_PROMPT env var")
        return env_prompt

    try:
        content = _PROMPT_FILE.read_text(encoding="utf-8").strip()
        if content:
            logger.info("System prompt loaded from %s", _PROMPT_FILE)
            return content
    except FileNotFoundError:
        logger.warning("System prompt file not found: %s — using fallback", _PROMPT_FILE)

    logger.info("System prompt using hardcoded fallback")
    return _FALLBACK
