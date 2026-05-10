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

# Hoặc chạy API server
uvicorn src.api.app:app --reload
```

## Tài liệu

| File | Nội dung |
|:-----|:---------|
| `AGENTS.md` | Hướng dẫn cho AI coding assistants |
| `docs/AGENT_ARCHITECTURE.md` | Deep dive kiến trúc ReAct, streaming, memory model |

## Giao diện

### CLI

```bash
python -m src.main
```

Interactive terminal chat, hiển thị trace summary sau mỗi câu hỏi.

### REST API + Frontend UI

```bash
uvicorn src.api.app:app --reload
```

- Frontend UI: `http://localhost:8000/`
- API docs (Swagger): `http://localhost:8000/docs`

#### API Endpoints

| Method | Path | Auth | Mô tả |
|--------|------|------|--------|
| `POST` | `/api/chat` | API Key | Non-streaming — trả về full answer + sources |
| `POST` | `/api/chat/stream` | API Key | Streaming via Server-Sent Events (SSE) |
| `GET` | `/health` | None | Health check (model, wiki_path, version, status) |
| `GET` | `/ready` | None | Readiness check (agent initialized, wiki accessible) |

#### Streaming Events

SSE stream phát các event type: `token`, `tool_call`, `tool_result`, `sources`, `done`, `error`.

## Tài liệu

| File | Nội dung |
|:-----|:---------|
| `AGENTS.md` | Hướng dẫn cho AI coding assistants |
| `docs/AGENT_ARCHITECTURE.md` | Deep dive kiến trúc ReAct, streaming, memory model |

## Monitoring

Tích hợp LangFuse v4 để theo dõi agent traces, user sessions, và tool usage. Cấu hình qua environment variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`). Optional — agent chạy bình thường nếu không cấu hình.

## Deployment (Docker)

Agent BE chạy như một Docker service riêng biệt.

### Standalone

```bash
# Từ innovation_hub_agent/
docker-compose up -d
```

### Kết nối với Hub BE

Để Hub BE gọi được Agent BE, cả hai phải cùng Docker network. Thêm network `innovation_hub_network` vào Hub BE's docker-compose:

```yaml
# Trong innovation_hub/docker-compose.yml, thêm agent-be service:
  agent-be:
    # ... (xem AGENTS.md để biết chi tiết)
    networks:
      - innovation_hub_network
    # Không cần expose port — Hub BE gọi qua internal network
```

Hoặc join network thủ công:
```bash
docker network connect innovation_hub_network innovation_hub_api
```

Lưu ý: Hub BE cần cấu hình `AGENT_BASE_URL=http://agent-be:8000` trong `.env`.

### Healthcheck

Docker healthcheck tự động kiểm tra `/health` mỗi 30 giây. Kiểm tra trạng thái:

```bash
docker inspect --format='{{.State.Health.Status}}' innovation_hub_agent
```

## Security

- **API Key**: `X-API-Key` header bắt buộc trên mọi `/api/*` endpoint. Service **từ chối khởi động** nếu `AGENT_API_KEY` không được cấu hình.
- **CORS**: Mặc định tắt (internal service). Bật qua `AGENT_CORS_ORIGINS` nếu cần.
- **Security headers**: Tự động thêm `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` trên mọi response.
- **API Docs**: `/docs` và `/redoc` tự động tắt khi `AGENT_ENV=production`.

## Cấu trúc project

```
src/
├── agent/
│   ├── config.py         # AgentConfig — safety limits, model settings
│   ├── core.py           # create_agent(), run_query(), stream_query()
│   ├── tools.py          # Wiki tool definitions + error handling
│   └── prompts.py        # System prompt loader
├── api/
│   ├── app.py            # FastAPI app — CORS, lifespan, static files
│   ├── routes/
│   │   └── chat.py       # /api/chat + /api/chat/stream endpoints
│   ├── schemas.py        # Pydantic models (ChatRequest, ChatResponse, ...)
│   └── static/
│       └── index.html    # Frontend UI với streaming visualization
├── monitoring/
│   └── langfuse.py       # LangFuse v4 — CallbackHandler + trace management
├── utils/
│   ├── wiki_fs.py        # WikiFilesystem — local .md file operations
│   └── logger.py         # Structured logging with RunTrace
└── main.py               # CLI entry point
tests/
├── conftest.py           # Shared fixtures (tmp_wiki, app_client, auth_headers)
├── test_auth.py          # Auth middleware tests
└── test_health.py        # Health & readiness endpoint tests
```

## Environment Variables

| Variable | Mô tả | Default |
|----------|--------|---------|
| `NVIDIA_API_KEY` | API key cho NVIDIA NIM | — |
| `WIKI_PATH` | Đường dẫn tuyệt đối đến wiki vault | — |
| `AGENT_API_KEY` | API key cho Hub BE auth (bắt buộc) | — |
| `AGENT_ENV` | Environment (`development` \| `production`) | `development` |
| `MODEL_NAME` | Tên model | `moonshotai/kimi-k2.5` |
| `NVIDIA_BASE_URL` | API endpoint | `https://integrate.api.nvidia.com/v1` |
| `MAX_TOOL_CALLS` | Giới hạn tool calls/query | `10` |
| `MAX_DEPTH` | Giới hạn độ sâu follow wiki links | `3` |
| `MAX_TOKENS` | Giới hạn tokens/response | `4096` |
| `LLM_MAX_RETRIES` | Số lần retry khi LLM lỗi | `3` |
| `TEMPERATURE` | LLM temperature | `0.0` |
| `TOOL_TIMEOUT_SECONDS` | Timeout cho mỗi tool call | `30` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LANGFUSE_PUBLIC_KEY` | LangFuse public key (optional) | — |
| `LANGFUSE_SECRET_KEY` | LangFuse secret key (optional) | — |
| `LANGFUSE_HOST` | LangFuse host URL | — |
| `AGENT_CORS_ORIGINS` | CORS origins, comma-separated (optional) | — |
| `AGENT_ALLOWED_IPS` | IP allowlist, comma-separated (optional) | — |

## Testing

```bash
# Unit tests (không cần API key hay NVIDIA key)
PYTHONPATH=. pytest tests/ -v
```

## Safety & Limits

- **Max tool calls**: Mặc định 10, configurable qua `MAX_TOOL_CALLS`
- **Max tokens**: Mặc định 4096, configurable qua `MAX_TOKENS`
- **Tool timeout**: Mặc định 30s, configurable qua `TOOL_TIMEOUT_SECONDS`
- **Link depth**: Tối đa 3 mức từ file gốc
- **Error handling**: Mỗi tool có graceful fallback — suggest search/list khi không tìm thấy

## Streaming API Usage

```python
from src.agent.core import create_agent, stream_query

agent, config = create_agent()
async for event in stream_query(agent, "query", "thread-1", config):
    print(event)  # {"type": "thinking"| "tool_call" | "tool_result" | "answer" | "error"}
```
