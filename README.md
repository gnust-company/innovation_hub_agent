# Innovation Hub Agent

AI Agent đọc Wiki vault (Obsidian) của Innovation Hub và trả lời câu hỏi sử dụng ReAct pattern với LangGraph.

## Kiến trúc

```
User Query
  → Agent (LLM via NVIDIA NIM)
    → Tool Call (read_file / search_wiki / ...)
      → WikiFilesystem (local .md files)
        → Observation + [[WikiLinks]] detected
          → Agent follows links if needed
            → Final Answer
```

Agent sử dụng 4 tools để đọc wiki vault:
- `read_file(path)` — Đọc file, tự động phát hiện `[[WikiLinks]]`
- `list_directory(path)` — Liệt kê files/thư mục
- `search_wiki(query)` — Tìm kiếm file theo tên
- `resolve_wikilink(link)` — Chuyển `[[Link]]` thành đường dẫn file

Wiki links được follow tự động (recursive, tối đa 3 mức sâu) khi cần thêm context.

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/gnust-company/innovation_hub_agent.git
cd innovation_hub_agent

# 2. Tạo virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Cài đặt dependencies
pip install -e ".[dev]"

# 4. Clone wiki vault
git clone https://github.com/gnust-company/innovation_hub_wiki.git ../innovation_hub_wiki

# 5. Cấu hình
cp .env.example .env
# Chỉnh .env: thêm NVIDIA_API_KEY, WIKI_PATH

# 6. Chạy CLI
python -m src.main
```

## Testing

```bash
# Unit tests (không cần API key)
pytest tests/test_wiki_fs.py tests/test_tools.py -v

# E2E tests (cần NVIDIA_API_KEY)
PYTHONPATH=. python tests/e2e_test.py
```

## Cấu trúc project

```
src/
├── agent/
│   ├── config.py         # AgentConfig — safety limits, model settings
│   ├── core.py           # create_agent(), run_query(), stream_query()
│   ├── tools.py          # Wiki tool definitions + error handling
│   └── prompts.py        # System prompt loader
├── utils/
│   ├── wiki_fs.py        # WikiFilesystem — local .md file operations
│   └── logger.py         # Structured logging with RunTrace
└── main.py               # CLI entry point
tests/
├── conftest.py           # Shared fixtures (tmp_wiki)
├── test_wiki_fs.py       # WikiFilesystem unit tests
├── test_tools.py         # Tool unit tests
├── test_agent.py         # Integration tests (needs API key)
└── e2e_test.py           # End-to-end test suite
```

## Environment Variables

| Variable | Mô tả | Default |
|----------|--------|---------|
| `NVIDIA_API_KEY` | API key cho NVIDIA NIM | — |
| `WIKI_PATH` | Đường dẫn tuyệt đối đến wiki vault | — |
| `MODEL_NAME` | Tên model | `moonshotai/kimi-k2.5` |
| `NVIDIA_BASE_URL` | API endpoint | `https://integrate.api.nvidia.com/v1` |
| `MAX_TOOL_CALLS` | Giới hạn tool calls/query | `10` |
| `MAX_TOKENS` | Giới hạn tokens/response | `4096` |
| `LLM_MAX_RETRIES` | Số lần retry khi LLM lỗi | `3` |
| `TEMPERATURE` | LLM temperature | `0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Safety & Limits

- **Max tool calls**: Mặc định 10, configurable qua `MAX_TOOL_CALLS`
- **Max tokens**: Mặc định 4096, configurable qua `MAX_TOKENS`
- **Link depth**: Tối đa 3 mức từ file gốc
- **Error handling**: Mỗi tool có graceful fallback — suggest search/list khi không tìm thấy

## Streaming

```python
from src.agent.core import create_agent, stream_query

agent, config = create_agent()
async for event in stream_query(agent, "query", "thread-1", config):
    print(event)  # {"type": "thinking"| "tool_call" | "tool_result" | "answer" | "error"}
```

Sẵn sàng cho SSE integration (Issue #9).
