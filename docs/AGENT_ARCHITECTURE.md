# Agent Architecture

## ReAct Loop

Agent sử dụng **ReAct (Reason + Act)** pattern qua LangGraph's `create_react_agent`:

```
1. LLM nhận query → quyết định dùng tool nào
2. Tool thực thi → trả về observation
3. LLM nhận observation → quyết định tiếp hoặc trả lời
4. Lặp lại cho đến khi có đủ context hoặc hết recursion_limit
```

Mỗi iteration = 1 tool call. `recursion_limit` (mặc định 10) giới hạn tổng số bước.

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

## Memory & State

- **MemorySaver** (in-memory checkpointer) cho multi-turn conversation
- Mỗi `thread_id` = 1 conversation riêng biệt
- State persist trong RAM, mất khi restart process
- Thiết kế stateless — history sẽ do Main BE quản lý khi integrate (Issue #92)

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
- `{"type": "tool_call", "name": "read_file", "args": {...}}` — Tool bắt đầu
- `{"type": "tool_result", "content": "..."}` — Tool hoàn thành
- `{"type": "answer", "content": "..."}` — Final answer
- `{"type": "error", "content": "..."}` — Error

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
- `files_read` — list files đã đọc
- `token_usage` — prompt/completion tokens
- `duration_seconds` — thời gian thực thi
- `error` — lỗi nếu có
