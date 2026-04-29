"""Chat endpoints — invoke and stream."""
import json
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from src.agent.core import run_query, stream_query
from src.api.schemas import ChatRequest, ChatResponse
from src.monitoring.langfuse import trace_agent_call

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    """Non-streaming chat — returns full answer with sources."""
    thread_id = req.thread_id or str(uuid.uuid4())
    agent = request.app.state.agent
    config = request.app.state.config

    with trace_agent_call(
        query=req.message,
        session_id=thread_id,
        user_id=req.user_metadata.username or None,
    ) as ctx:
        output = run_query(
            agent, req.message, thread_id, config,
            handler=ctx.handler, user_id=req.user_metadata.username or "",
        )
        result = output["result"]
        trace = output["trace"]

        answer = ""
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                answer = msg.content
                break

        if ctx.span:
            ctx.span.update(output=answer)

    return ChatResponse(answer=answer, sources=trace.files_read, thread_id=thread_id)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Streaming chat via Server-Sent Events."""
    thread_id = req.thread_id or str(uuid.uuid4())
    agent = request.app.state.agent
    config = request.app.state.config

    with trace_agent_call(
        query=req.message,
        session_id=thread_id,
        user_id=req.user_metadata.username or None,
    ) as ctx:

        full_answer = ""

        async def event_generator():
            nonlocal full_answer
            try:
                async for event in stream_query(
                    agent, req.message, thread_id, config,
                    handler=ctx.handler, user_id=req.user_metadata.username or "",
                ):
                    if event["type"] == "thinking":
                        full_answer += event.get("content", "")
                        yield {"data": json.dumps(
                            {"type": "token", "content": event["content"]},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "tool_call":
                        yield {"data": json.dumps(
                            {"type": "tool_call", "name": event.get("name", "")},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "tool_result":
                        yield {"data": json.dumps(
                            {"type": "tool_result", "content": event["content"]},
                            ensure_ascii=False,
                        )}
                    elif event["type"] == "error":
                        yield {"data": json.dumps(
                            {"type": "error", "content": event["content"]},
                            ensure_ascii=False,
                        )}

                yield {"data": json.dumps({"type": "sources", "files": []}, ensure_ascii=False)}
                yield {"data": json.dumps({"type": "done"}, ensure_ascii=False)}

            except Exception as e:
                yield {"data": json.dumps(
                    {"type": "error", "content": str(e)},
                    ensure_ascii=False,
                )}
            finally:
                if ctx.span:
                    ctx.span.update(output=full_answer)

    return EventSourceResponse(event_generator())
