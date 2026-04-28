"""Chat endpoints — invoke and stream."""
import json
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from src.agent.core import run_query, stream_query
from src.api.schemas import ChatRequest, ChatResponse, StreamEvent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    """Non-streaming chat — returns full answer with sources."""
    thread_id = req.thread_id or str(uuid.uuid4())

    agent = request.app.state.agent
    config = request.app.state.config

    output = run_query(agent, req.message, thread_id, config)
    result = output["result"]
    trace = output["trace"]

    # Extract final answer from last AI message
    answer = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            answer = msg.content
            break

    return ChatResponse(
        answer=answer,
        sources=trace.files_read,
        thread_id=thread_id,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Streaming chat via Server-Sent Events."""
    thread_id = req.thread_id or str(uuid.uuid4())

    agent = request.app.state.agent
    config = request.app.state.config

    files_read: list[str] = []

    async def event_generator():
        try:
            async for event in stream_query(agent, req.message, thread_id, config):
                if event["type"] == "thinking":
                    yield {"data": json.dumps(
                        {"type": "token", "content": event["content"]},
                        ensure_ascii=False,
                    )}

                elif event["type"] == "tool_call":
                    name = event.get("name", "")
                    yield {"data": json.dumps(
                        {"type": "tool_call", "name": name},
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

            # Send sources at the end
            yield {"data": json.dumps(
                {"type": "sources", "files": files_read},
                ensure_ascii=False,
            )}
            yield {"data": json.dumps({"type": "done"}, ensure_ascii=False)}

        except Exception as e:
            yield {"data": json.dumps(
                {"type": "error", "content": str(e)},
                ensure_ascii=False,
            )}

    return EventSourceResponse(event_generator())
