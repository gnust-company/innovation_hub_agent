# Innovation Hub Agent

AI Agent đọc Wiki vault của Innovation Hub và trả lời câu hỏi sử dụng ReAct pattern với LangGraph.

## Kiến trúc

```
User Query → Agent (LLM) → [Tool Call] → GitHub Wiki API → Observation → Agent → ... → Answer
```

Agent sử dụng 4 tools để đọc wiki:
- `read_file(path)` — Đọc file từ wiki repo
- `list_directory(path)` — Liệt kê files trong thư mục
- `search_wiki(query)` — Tìm kiếm file trong wiki
- `resolve_wikilink(link)` — Chuyển `[[Link]]` thành đường dẫn file

Wiki links được follow tự động (recursive) khi cần thêm context.

## Cài đặt

```bash
# Clone repo
git clone https://github.com/gnust-company/innovation_hub_agent.git
cd innovation_hub_agent

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate

# Cài đặt
pip install -e ".[dev]"

# Cấu hình environment
cp .env.example .env
# Chỉnh sửa .env với token/API key thực tế
```

## Chạy

```bash
python -m src.main
```

## Cấu trúc project

```
src/
├── agent/
│   ├── core.py          # ReAct agent setup
│   ├── tools.py         # Wiki tool definitions
│   └── prompts.py       # System prompt loader
├── utils/
│   └── github_api.py    # GitHub API wrapper
└── main.py              # Entry point / CLI
tests/
├── test_tools.py
├── test_agent.py
└── test_wikilink.py
```

## Environment Variables

| Variable | Mô tả | Default |
|----------|--------|---------|
| `GITHUB_TOKEN` | GitHub PAT để đọc wiki repo | — |
| `MODEL_PROVIDER` | LLM provider | `openai` |
| `OPENAI_API_KEY` | API key cho LLM | — |
| `OPENAI_BASE_URL` | Custom endpoint (DeepSeek, etc.) | — |
| `MODEL_NAME` | Tên model | `gpt-4o-mini` |
| `WIKI_REPO` | Wiki repository | `gnust-company/innovation_hub_wiki` |
| `MAX_TOOL_CALLS` | Giới hạn tool calls/query | `10` |
| `MAX_DEPTH` | Độ sâu recursive link following | `3` |
