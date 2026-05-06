"""Chat endpoints — invoke and stream."""
import json
import uuid

from fastapi import APIRouter, Header, Request
from sse_starlette.sse import EventSourceResponse

from langfuse import propagate_attributes

from src.agent.core import create_agent_with_key, run_query, stream_query
from src.api.schemas import ChatRequest, ChatResponse
from src.monitoring.langfuse import trace_agent_call, start_trace, end_trace

def _friendly_error(exc: Exception) -> str:
    """Convert raw LLM exceptions to short error codes for FE i18n."""
    msg = str(exc).lower()
    if "403" in msg or "401" in msg or "unauthorized" in msg or "authentication" in msg or "authorization failed" in msg:
        return "AUTH_FAILED"
    if "rate_limit" in msg or "429" in msg:
        return "RATE_LIMITED"
    if "timeout" in msg or "timed out" in msg:
        return "TIMEOUT"
    if "connection" in msg or "connect" in msg:
        return "CONNECTION_ERROR"
    return "STREAM_ERROR"


router = APIRouter()


def _parse_messages(req: ChatRequest) -> list[dict]:
    """Convert ChatRequest.messages (Pydantic) to list[dict] for core."""
    return [{"role": m.role, "content": m.content} for m in req.messages]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    request: Request,
    x_llm_api_key: str = Header(..., alias="X-LLM-API-Key"),
):
    """Non-streaming chat — returns full answer with sources."""
    thread_id = req.thread_id or str(uuid.uuid4())
    config = request.app.state.config
    agent, _ = create_agent_with_key(x_llm_api_key, config)
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
async def chat_stream(
    req: ChatRequest,
    request: Request,
    x_llm_api_key: str = Header(..., alias="X-LLM-API-Key"),
):
    """Streaming chat via Server-Sent Events."""
    thread_id = req.thread_id or str(uuid.uuid4())
    config = request.app.state.config
    agent, _ = create_agent_with_key(x_llm_api_key, config)
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
                    {"type": "error", "content": _friendly_error(e)},
                    ensure_ascii=False,
                )}
            finally:
                end_trace(ctx)

    return EventSourceResponse(event_generator())


@router.post("/validate-key")
async def validate_key(
    request: Request,
    x_llm_api_key: str = Header(..., alias="X-LLM-API-Key"),
):
    """Check if the provided LLM API key is valid via a minimal chat completion."""
    import httpx

    config = request.app.state.config
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {x_llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.model_name,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 10,
                },
            )
        if resp.status_code == 200:
            return {"valid": True}
        if resp.status_code in (401, 403):
            return {"valid": False, "reason": "invalid_key"}
        return {"valid": False, "reason": "error", "detail": f"API returned HTTP {resp.status_code}"}
    except httpx.ConnectError:
        return {"valid": False, "reason": "llm_unreachable"}
    except httpx.ReadTimeout:
        return {"valid": False, "reason": "error", "detail": "LLM request timed out during key validation"}
    except Exception as exc:
        return {"valid": False, "reason": "error", "detail": str(exc)[:200]}
