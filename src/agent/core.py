"""Core ReAct agent setup using LangGraph — tools loaded from MCP server."""
import os
import uuid

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.agent.config import AgentConfig
from src.agent.prompts import load_system_prompt
from src.utils.logger import logger, setup_logging, trace_run

try:
    from copilotkit import CopilotKitState
except ImportError:
    CopilotKitState = None

_mcp_client: MultiServerMCPClient | None = None
_mcp_tools: list = []
_system_prompt: str = ""
_setup_done = False
_graph = None  # Compiled StateGraph for AG-UI (CopilotKit)


def _ensure_setup():
    """One-time logging setup."""
    global _setup_done
    if _setup_done:
        return
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    _setup_done = True


async def init_mcp(config: AgentConfig):
    """Load system prompt from local file, then connect to MCP for tools."""
    global _mcp_client, _mcp_tools, _system_prompt, _graph

    _system_prompt = load_system_prompt()

    mcp_url = config.mcp_url
    logger.info("Connecting to MCP server at %s", mcp_url)

    try:
        _mcp_client = MultiServerMCPClient(
            {"innovation_hub": {"url": f"{mcp_url}/mcp", "transport": "http"}}
        )
        _mcp_tools = await _mcp_client.get_tools()
        tool_names = [t.name for t in _mcp_tools]
        logger.info("Loaded %d tools from MCP: %s", len(_mcp_tools), tool_names)
    except Exception as e:
        logger.error("MCP connection failed: %s — agent starting without tools", e)
        _mcp_tools = []

    _graph = _build_agui_graph(config)


async def shutdown_mcp():
    """Release MCP client reference.

    MultiServerMCPClient is stateless — each tool call creates a new HTTP
    session, so there is no persistent connection to close.  Setting to None
    is sufficient to release the config reference.
    """
    global _mcp_client
    if _mcp_client:
        _mcp_client = None
        logger.info("MCP client reference released")


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


def _resolve_llm_key(config: RunnableConfig) -> str:
    """Extract LLM API key from config — supports per-user keys via AG-UI forwardedProps."""
    forwarded = config.get("configurable", {}).get("forwardedProps", {})
    key = forwarded.get("llmApiKey", "") if isinstance(forwarded, dict) else ""
    return key or os.getenv("NVIDIA_API_KEY", "")


# --- AG-UI Graph (CopilotKit) ---

class _AgentState(MessagesState if CopilotKitState is None else CopilotKitState):
    """State for AG-UI graph — extends CopilotKitState when available."""
    pass


async def _agui_chat_node(state: _AgentState, config: RunnableConfig):
    """Chat node for AG-UI — creates LLM per-request from config."""
    agent_config = AgentConfig()
    llm_key = _resolve_llm_key(config)
    if not llm_key:
        return Command(goto=END, update={"messages": []})

    llm = create_llm(llm_key, agent_config)

    # Bind CopilotKit frontend actions + MCP backend tools
    fe_tools = []
    if CopilotKitState is not None and hasattr(state, "get"):
        fe_tools = state.get("copilotkit", {}).get("actions", [])
    model_with_tools = llm.bind_tools([*fe_tools, *_mcp_tools])

    system_msg = SystemMessage(content=_system_prompt)
    response = await model_with_tools.ainvoke(
        [system_msg, *state["messages"]], config
    )

    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        fe_tool_names = {a["name"] for a in fe_tools} if fe_tools else set()
        has_backend_calls = any(tc["name"] not in fe_tool_names for tc in tool_calls)
        if has_backend_calls:
            return Command(goto="tool_node", update={"messages": [response]})
    return Command(goto=END, update={"messages": [response]})


def _should_route_to_tools(state):
    """No-op router — handled by Command in chat_node."""
    return END


def _build_agui_graph(config: AgentConfig):
    """Build compiled StateGraph for AG-UI (CopilotKit)."""
    if not _mcp_tools:
        logger.warning("Building AG-UI graph without MCP tools")

    tool_node = ToolNode(_mcp_tools, handle_tool_errors=True) if _mcp_tools else ToolNode([])

    graph = StateGraph(_AgentState)
    graph.add_node("chat_node", _agui_chat_node)
    graph.add_node("tool_node", tool_node)
    graph.add_edge("tool_node", "chat_node")
    graph.set_entry_point("chat_node")

    return graph.compile(checkpointer=MemorySaver())


def get_agui_graph():
    """Return compiled AG-UI graph — raises if not initialized."""
    if _graph is None:
        raise RuntimeError("AG-UI graph not initialized — call init_mcp() first")
    return _graph


# --- Legacy agent creation (Hub BE proxy) ---

def create_agent_with_key(api_key: str, config: AgentConfig | None = None):
    """Create a ReAct agent using a per-request LLM API key."""
    config = config or AgentConfig()
    _ensure_setup()

    if not _mcp_tools:
        logger.warning("Creating agent without MCP tools — capabilities will be limited")

    llm = create_llm(api_key, config)
    tool_node = ToolNode(_mcp_tools, handle_tool_errors=True) if _mcp_tools else []
    agent = create_react_agent(
        model=llm,
        tools=tool_node,
        prompt=_system_prompt,
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
    """Build LangGraph invoke config."""
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
    """Stream agent execution with intermediate steps visible."""
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

                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    has_tc = bool(getattr(chunk, "tool_calls", None))
                    logger.info(f"[EVENT] {kind}: content_len={len(chunk.content) if chunk and hasattr(chunk, 'content') and chunk.content else 0}, tool_calls={has_tc}")
                elif kind == "on_chat_model_end":
                    msg = data.get("output")
                    tc_list = getattr(msg, "tool_calls", None) if msg else None
                    logger.info(f"[EVENT] {kind}: tool_calls={tc_list}, finish_reason={getattr(msg, 'response_metadata', {}).get('finish_reason') if msg else None}")
                elif kind == "on_tool_start":
                    logger.info(f"[EVENT] {kind}: name={event.get('name')}")
                elif kind == "on_tool_end":
                    output = data.get("output", {})
                    status = getattr(output, "status", None)
                    if status == "error":
                        logger.warning(f"[EVENT] on_tool_end ERROR: name={event.get('name')}")
                    else:
                        logger.info(f"[EVENT] on_tool_end: name={event.get('name')}")
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

                elif kind == "on_chain_end":
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        messages = output.get("messages", [])
                        if isinstance(messages, list) and messages:
                            last = messages[-1]
                            msg_content = getattr(last, "content", "")
                            if "Sorry, need more steps" in str(msg_content):
                                yield {"type": "limit_reached"}

            yield {"type": "sources", "files": trace.files_read}

        except Exception as e:
            error_msg = str(e)
            logger.error("Stream error: %s", error_msg)
            # Check if this is a tool/MCP connectivity issue
            if "TaskGroup" in error_msg or "Connection" in error_msg or "connect" in error_msg.lower():
                yield {"type": "error", "content": "Hệ thống đang bảo trì, tôi chưa thể truy xuất thông tin chi tiết lúc này. Vui lòng thử lại sau."}
            else:
                yield {"type": "error", "content": error_msg}
