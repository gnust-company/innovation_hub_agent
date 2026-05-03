"""Chat endpoints — invoke and stream."""
import json
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from langfuse import propagate_attributes

from src.agent.core import run_query, stream_query
from src.api.schemas import ChatRequest, ChatResponse
from src.monitoring.langfuse import trace_agent_call, start_trace, end_trace

router = APIRouter()


def _parse_messages(req: ChatRequest) -> list[dict]:
    """Convert ChatRequest.messages (Pydantic) to list[dict] for core."""
    return [{"role": m.role, "content": m.content} for m in req.messages]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    """Non-streaming chat — returns full answer with sources."""
    thread_id = req.thread_id or str(uuid.uuid4())
    agent = request.app.state.agent
    config = request.app.state.config
    messages = _parse_messages(req)

    with trace_agent_call(
        session_id=thread_id,
        user_id=req.user_metadata.username or None,
    ) as ctx:
        output = run_query(
            agent, req.message, thread_id, config,
            messages=messages,
            handler=ctx.handler, user_id=req.user_metadata.username or "",
        )
        result = output["result"]
        trace = output["trace"]

        answer = ""
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                answer = msg.content
                break

    return ChatResponse(answer=answer, sources=trace.files_read, thread_id=thread_id)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Streaming chat via Server-Sent Events."""
    thread_id = req.thread_id or str(uuid.uuid4())
    agent = request.app.state.agent
    config = request.app.state.config
    messages = _parse_messages(req)

    async def event_generator():
        ctx = start_trace(
            session_id=thread_id,
            user_id=req.user_metadata.username or None,
        )
        with propagate_attributes(
            user_id=ctx.user_id,
            session_id=ctx.session_id,
            trace_name="agent_query",
        ):
            try:
                async for event in stream_query(
                    agent, req.message, thread_id, config,
                    messages=messages,
                    handler=ctx.handler, user_id=req.user_metadata.username or "",
                ):
                    if event["type"] == "thinking":
                        yield {"data": json.dumps(
                            {"type": "token", "content": event["content"]},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "tool_call":
                        yield {"data": json.dumps(
                            {"type": "tool_call", "name": event.get("name", ""),
                             "args": event.get("args", {}), "run_id": event.get("run_id", "")},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "tool_result":
                        yield {"data": json.dumps(
                            {"type": "tool_result", "content": event["content"],
                             "run_id": event.get("run_id", "")},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "sources":
                        yield {"data": json.dumps(
                            {"type": "sources", "files": event["files"]},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "error":
                        yield {"data": json.dumps(
                            {"type": "error", "content": event["content"]},
                            ensure_ascii=False,
                        )}

                yield {"data": json.dumps({"type": "done"}, ensure_ascii=False)}

            except Exception as e:
                yield {"data": json.dumps(
                    {"type": "error", "content": str(e)},
                    ensure_ascii=False,
                )}
            finally:
                end_trace(ctx)

    return EventSourceResponse(event_generator())
