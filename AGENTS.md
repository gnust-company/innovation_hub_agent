# AGENTS.md — AI Coding Agent Reference

## Purpose

Innovation Hub Agent là một stateless AI backend đọc Obsidian Wiki vault và trả lời câu hỏi. Nó là một microservice trong hệ sinh thái Innovation Hub, được gọi bởi Hub BE (FastAPI backend chính) qua HTTP + SSE.

## Architecture

```
Hub BE (port 8000)
  → POST /api/chat/stream (X-API-Key auth)
    → Agent BE (LangGraph ReAct)
      → Wiki Tools → Local .md files (read-only)
      → NVIDIA NIM LLM API
    ← SSE stream (token, tool_call, tool_result, sources, done, error)
  ← Forward to Frontend
```

Agent BE **không persist state** giữa các requests. Hub BE gửi full `messages[]` mỗi lần, Agent xử lý xong trả kết quả.

## Key Files

| File | Role |
|------|------|
| `src/api/app.py` | FastAPI app — lifespan, middleware, /health, /ready |
| `src/api/routes/chat.py` | /api/chat + /api/chat/stream endpoints |
| `src/api/deps.py` | Auth (X-API-Key), IP allowlist |
| `src/api/schemas.py` | Pydantic models (ChatRequest, ChatResponse, HealthResponse) |
| `src/agent/core.py` | LangGraph agent creation + run_query/stream_query |
| `src/agent/config.py` | AgentConfig dataclass (env var overrides) |
| `src/agent/tools.py` | Wiki tools: read_file, list_directory, search_wiki, resolve_wikilink |
| `src/agent/prompts.py` | System prompt loader |
| `src/monitoring/langfuse.py` | LangFuse v4 tracing |
| `src/utils/logger.py` | Structured logging (JSON in production) |
| `src/utils/wiki_fs.py` | WikiFilesystem — .md file operations |
| `src/main.py` | CLI entry point |
| `docs/AGENT_ARCHITECTURE.md` | Deep dive kiến trúc ReAct, streaming, memory model |

## Conventions

- **Stateless**: No cross-request state. Every request includes full conversation history in `messages[]`.
- **Auth required**: All `/api/*` endpoints require `X-API-Key` header. Service crashes on startup if `AGENT_API_KEY` env var is missing.
- **SSE only for streaming**: `/api/chat/stream` uses `sse_starlette` EventSourceResponse. Data format: `data: {"type": "...", ...}\n\n`.
- **Tool error handling**: Each tool catches exceptions and returns helpful error messages suggesting alternative actions.
- **Internal thread_id**: Each request gets a unique UUID for LangGraph's MemorySaver to prevent state leakage. Hub BE's `thread_id` is passed to Langfuse only.

## Testing

```bash
PYTHONPATH=. pytest tests/ -v
```

Tests use `FastAPI.TestClient` with mocked env vars. Agent is NOT initialized in tests (no LLM key needed). Fixtures in `tests/conftest.py` provide `app_client`, `auth_headers`, and `tmp_wiki`.

## Known Limitations

- **Wiki path dependency**: Requires local filesystem access to wiki vault. In Docker, wiki is mounted read-only from host.
- **No cross-request memory**: Agent cannot remember previous conversations. Hub BE maintains all history.
- **LLM dependency**: NVIDIA NIM API must be available. No local fallback.
- **Single LLM provider**: Only NVIDIA NIM (OpenAI-compatible) is supported.
