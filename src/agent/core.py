"""Core ReAct agent setup using LangGraph."""
import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from src.agent.config import AgentConfig
from src.agent.prompts import load_system_prompt
from src.agent.tools import read_file, list_directory, search_wiki, resolve_wikilink
from src.utils.wiki_fs import WikiFilesystem
from src.utils.logger import logger, setup_logging, trace_run, RunTrace
from src.monitoring.langfuse import AgentTrace

TOOLS = [read_file, list_directory, search_wiki, resolve_wikilink]


def create_agent(config: AgentConfig | None = None):
    """Create and return a ReAct agent with wiki tools."""
    config = config or AgentConfig()

    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    wiki_path = os.getenv("WIKI_PATH")
    if not wiki_path:
        raise ValueError("WIKI_PATH environment variable is not set")
    wiki = WikiFilesystem(wiki_path)

    system_prompt = load_system_prompt(wiki)

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is required. Get one at build.nvidia.com")

    llm = ChatOpenAI(
        model=config.model_name,
        api_key=api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        max_retries=config.llm_max_retries,
    )

    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=system_prompt,
        checkpointer=MemorySaver(),
    )

    return agent, config


def run_query(agent, query: str, thread_id: str, config: AgentConfig,
              user_metadata: dict | None = None) -> dict:
    """Run a single query with safety limits, structured logging, and Langfuse tracking."""
    meta = user_metadata or {}
    lf_trace = AgentTrace(
        query=query,
        thread_id=thread_id,
        user_id=meta.get("user_id", ""),
        username=meta.get("username", ""),
        role=meta.get("role", ""),
    )

    with trace_run(query) as trace:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": config.max_tool_calls,
            },
        )

        for msg in result["messages"]:
            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace.record_tool(tc["name"], tc.get("args", {}))
                    lf_trace.on_tool_start(tc["name"], tc.get("args", {}))
                    lf_trace.on_tool_end(str(tc.get("args", {})))

        token_meta = {}
        for msg in reversed(result["messages"]):
            if msg.type == "ai":
                meta_data = getattr(msg, "response_metadata", {})
                if meta_data:
                    token_meta = meta_data.get("token_usage", {})
                    if token_meta:
                        trace.token_usage = token_meta
                break

    # Extract final answer
    answer = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            answer = msg.content
            break

    lf_trace.on_complete(answer, trace.files_read, token_meta or None)

    return {"result": result, "trace": trace}


async def stream_query(agent, query: str, thread_id: str, config: AgentConfig,
                       user_metadata: dict | None = None):
    """Stream agent execution with intermediate steps visible and Langfuse tracking."""
    meta = user_metadata or {}
    lf_trace = AgentTrace(
        query=query,
        thread_id=thread_id,
        user_id=meta.get("user_id", ""),
        username=meta.get("username", ""),
        role=meta.get("role", ""),
    )

    with trace_run(query) as trace:
        try:
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": query}]},
                config={
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": config.max_tool_calls,
                },
                version="v2",
            ):
                kind = event.get("event")
                data = event.get("data", {})

                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        lf_trace.on_thinking_chunk(chunk.content)
                        yield {"type": "thinking", "content": chunk.content}

                elif kind == "on_tool_start":
                    name = data.get("name", "")
                    inp = data.get("input", {})
                    trace.record_tool(name, inp)
                    lf_trace.on_tool_start(name, inp)
                    yield {"type": "tool_call", "name": name, "args": inp}

                elif kind == "on_tool_end":
                    output = data.get("output", {})
                    content = output.content if hasattr(output, "content") else str(output)
                    lf_trace.on_tool_end(content[:2000])
                    yield {"type": "tool_result", "content": content[:500]}

            lf_trace.on_complete("", trace.files_read)

        except Exception as e:
            logger.error(f"Stream error: {e}")
            lf_trace.on_error(str(e))
            yield {"type": "error", "content": str(e)}
