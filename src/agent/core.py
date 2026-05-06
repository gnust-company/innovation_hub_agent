"""Core ReAct agent setup using LangGraph — stateless, gateway-ready."""
import os
import uuid

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from src.agent.config import AgentConfig
from src.agent.prompts import load_system_prompt
from src.agent.tools import read_file, list_directory, search_wiki, resolve_wikilink
from src.utils.wiki_fs import WikiFilesystem
from src.utils.logger import logger, setup_logging, trace_run

TOOLS = [read_file, list_directory, search_wiki, resolve_wikilink]

_setup_done = False


def _ensure_setup():
    """One-time setup (logging, wiki validation, system prompt)."""
    global _setup_done
    if _setup_done:
        return
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    _setup_done = True


def _load_prompt() -> str:
    """Load system prompt from wiki (validates WIKI_PATH)."""
    wiki_path = os.getenv("WIKI_PATH")
    if not wiki_path:
        raise ValueError("WIKI_PATH environment variable is not set")
    return load_system_prompt(WikiFilesystem(wiki_path))


def create_llm(api_key: str, config: AgentConfig | None = None) -> ChatOpenAI:
    """Create a ChatOpenAI instance with the given API key."""
    config = config or AgentConfig()
    return ChatOpenAI(
        model=config.model_name,
        api_key=api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        max_retries=config.llm_max_retries,
    )


def create_agent_with_key(api_key: str, config: AgentConfig | None = None):
    """Create a ReAct agent using a per-request LLM API key."""
    config = config or AgentConfig()
    _ensure_setup()

    llm = create_llm(api_key, config)
    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=_load_prompt(),
        checkpointer=MemorySaver(),
    )
    return agent, config


def create_agent(config: AgentConfig | None = None):
    """Create a ReAct agent using NVIDIA_API_KEY from env (backward compat)."""
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is required. Get one at build.nvidia.com")
    return create_agent_with_key(api_key, config)


def _last_user_content(messages: list[dict]) -> str:
    """Extract content of the last user message for logging/tracing."""
    return next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")


def _build_langgraph_messages(
    message: str,
    messages: list[dict],
) -> list[dict]:
    """Build LangGraph input from request.

    If messages[] is provided → use as full conversation history.
    If messages[] is empty → fallback to single-turn with message field.
    """
    if messages:
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    if message:
        logger.warning("Using deprecated 'message' field — switch to 'messages[]'")
        return [{"role": "user", "content": message}]

    raise ValueError("Either 'messages' or 'message' must be provided")


def _build_config(
    thread_id: str,
    config: AgentConfig,
    handler=None,
    user_id: str = "",
    session_id: str = "",
) -> dict:
    """Build LangGraph invoke config.

    Uses a unique thread_id per request so MemorySaver never loads stale state
    from a previous request. The Hub BE's thread_id is passed to Langfuse only.
    """
    cfg = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.max_tool_calls,
    }
    if handler:
        cfg["callbacks"] = [handler]
        cfg["run_name"] = "agent_query"
        cfg["metadata"] = {
            "langfuse_session_id": session_id or thread_id,
            "langfuse_user_id": user_id or "",
        }
    return cfg


def run_query(
    agent,
    message: str,
    thread_id: str,
    config: AgentConfig,
    messages: list[dict] | None = None,
    handler=None,
    user_id: str = "",
) -> dict:
    """Run a single query with safety limits and structured logging."""
    langgraph_msgs = _build_langgraph_messages(message, messages or [])
    # Unique thread_id per request — prevents MemorySaver state leakage
    internal_tid = str(uuid.uuid4())

    with trace_run(_last_user_content(langgraph_msgs)) as trace:
        result = agent.invoke(
            {"messages": langgraph_msgs},
            config=_build_config(internal_tid, config, handler, user_id, thread_id),
        )

        for msg in result["messages"]:
            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace.record_tool(tc["name"], tc.get("args", {}))

        for msg in reversed(result["messages"]):
            if msg.type == "ai":
                meta = getattr(msg, "response_metadata", {})
                if meta:
                    token_meta = meta.get("token_usage", {})
                    if token_meta:
                        trace.token_usage = token_meta
                break

    return {"result": result, "trace": trace}


async def stream_query(
    agent,
    message: str,
    thread_id: str,
    config: AgentConfig,
    messages: list[dict] | None = None,
    handler=None,
    user_id: str = "",
):
    """Stream agent execution with intermediate steps visible.

    Yields events: thinking, tool_call, tool_result, sources, error.
    The 'sources' event contains actual wiki files read during execution.
    """
    langgraph_msgs = _build_langgraph_messages(message, messages or [])
    internal_tid = str(uuid.uuid4())

    with trace_run(_last_user_content(langgraph_msgs)) as trace:
        try:
            async for event in agent.astream_events(
                {"messages": langgraph_msgs},
                config=_build_config(internal_tid, config, handler, user_id, thread_id),
                version="v2",
            ):
                kind = event.get("event")
                data = event.get("data", {})

                # Debug: log ALL events to trace tool call flow
                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    has_tc = bool(getattr(chunk, "tool_calls", None))
                    logger.info(f"[EVENT] {kind}: content_len={len(chunk.content) if chunk and hasattr(chunk, 'content') and chunk.content else 0}, tool_calls={has_tc}")
                elif kind == "on_chat_model_end":
                    msg = data.get("output")
                    tc_list = getattr(msg, "tool_calls", None) if msg else None
                    logger.info(f"[EVENT] {kind}: tool_calls={tc_list}, finish_reason={getattr(msg, 'response_metadata', {}).get('finish_reason') if msg else None}")
                elif kind in ("on_tool_start", "on_tool_end"):
                    logger.info(f"[EVENT] {kind}: name={event.get('name')}")
                else:
                    logger.debug(f"[EVENT] {kind}")

                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield {"type": "thinking", "content": chunk.content}

                elif kind == "on_tool_start":
                    name = event.get("name", "")
                    inp = data.get("input", {})
                    trace.record_tool(name, inp)
                    yield {"type": "tool_call", "name": name, "args": inp, "run_id": event.get("run_id", "")}

                elif kind == "on_tool_end":
                    output = data.get("output", {})
                    content = output.content if hasattr(output, "content") else str(output)
                    yield {"type": "tool_result", "content": content, "run_id": event.get("run_id", "")}

            # Emit actual sources from files read during execution
            yield {"type": "sources", "files": trace.files_read}

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {"type": "error", "content": str(e)}
