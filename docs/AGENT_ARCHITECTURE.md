# Agent Architecture

## Overview

Agent BE là stateless, gateway-ready AI backend. Hub BE owns all session/message history trong PostgreSQL và gửi full `messages[]` mỗi request. Agent BE không persist state giữa các requests.

## ReAct Loop

Agent sử dụng **ReAct (Reason + Act)** pattern qua LangGraph's `create_react_agent`:

```
1. LLM nhận query + history → quyết định dùng tool nào
2. Tool thực thi → trả về observation
3. LLM nhận observation → quyết định tiếp hoặc trả lời
4. Lặp lại cho đến khi có đủ context hoặc hết recursion_limit
```

Mỗi iteration = 1 tool call. `recursion_limit` (mặc định 10) giới hạn tổng số bước.

## Authentication & Security

- **API Key**: `X-API-Key` header required, validated against `AGENT_API_KEY` env var
- **CORS**: Disabled by default (internal services). Enable via `AGENT_CORS_ORIGINS` if needed
- **IP Allowlist**: Optional, via `AGENT_ALLOWED_IPS` env var

## Request Contract

### Messages[] (gateway mode)
Hub BE gửi full conversation history trong `messages[]` array:
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "thread_id": "uuid-from-hub-be",
  "user_metadata": {...}
}
```

### Backward Compatibility
Nếu `messages[]` trống, fallback sang `message` field (single-turn). Deprecated — log warning.

## Memory & State

- **MemorySaver** (in-memory checkpointer) cho **intra-request reasoning only**
  - Tool calling loops: agent calls tool → gets result → calls another tool → final answer
  - All within one `stream_query()` / `run_query()` invocation
- **MemorySaver is NOT for cross-request persistence**
  - Unique `thread_id` generated per request → prevents state leakage
  - Hub BE's `thread_id` passed to Langfuse tracing only
- **Hub BE owns all history** in PostgreSQL, sends full `messages[]` each request

## Wiki Link Following

Khi `read_file` đọc 1 file, nó tự động:
1. Parse `[[WikiLinks]]` từ nội dung bằng regex
2. Hiển thị links ở cuối output: `**Liên kết phát hiện trong file:**`
3. Agent (LLM) quyết định follow link nào dựa trên relevance

### Depth Control
- Tối đa 3 mức sâu từ file gốc
- Không đọc lại file đã đọc trong cùng conversation
- Nếu sau 3 lần follow vẫn chưa đủ → trả lời bằng info hiện có

### Link Resolution
- `[[SimpleLink]]` → fuzzy match theo filename stem
- `[[folder/Link]]` → direct path match
- `[[Link|Display Text]]` → chỉ lấy phần link

## Tools

| Tool | Mục đích | Khi nào dùng |
|------|----------|-------------|
| `read_file(path)` | Đọc nội dung file | Khi biết chính xác path hoặc sau khi resolve link |
| `list_directory(path)` | Liệt kê thư mục | Khi cần browse cấu trúc wiki |
| `search_wiki(query)` | Tìm file theo tên | Khi không biết chính xác path |
| `resolve_wikilink(link)` | Chuyển `[[Link]]` → path | Khi follow wiki link từ nội dung |

### Error Handling
Mỗi tool có try/except wrapper:
- Wiki unavailable → `"Wiki vault is unavailable"`
- File not found → suggest `search_wiki()` hoặc `list_directory()`
- Link không resolve được → suggest `search_wiki()`

## Streaming

`stream_query()` là async generator, yield events:
- `{"type": "thinking", "content": "..."}` — LLM token stream
- `{"type": "tool_call", "name": "...", "args": {...}}` — Tool bắt đầu
- `{"type": "tool_result", "content": "..."}` — Tool hoàn thành
- `{"type": "sources", "files": [...]}` — Wiki files đã đọc (trước `done`)
- `{"type": "error", "content": "..."}` — Error

`sources` luôn được emit (array rỗng nếu không đọc file nào).

Sử dụng LangGraph's `astream_events(version="v2")`.

## Config

`AgentConfig` dataclass, override bằng env vars:

```python
config = AgentConfig()
config.max_tool_calls   # 10 — giới hạn iterations
config.max_tokens       # 4096 — giới hạn response length
config.tool_timeout_seconds  # 30 — timeout cho tool execution
config.llm_max_retries # 3 — retry khi LLM fail
```

## Structured Logging

Mỗi query được trace qua `RunTrace`:
- `run_id` — unique ID
- `query` — câu hỏi gốc
- `tools_called` — list tools đã gọi
- `files_read` — list files đã đọc (populated cho cả non-streaming và streaming)
- `token_usage` — prompt/completion tokens
- `duration_seconds` — thời gian thực thi
- `error` — lỗi nếu có
