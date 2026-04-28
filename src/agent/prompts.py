"""System prompt loader — reads AGENT_GUIDE.md from the wiki vault."""
from src.utils.wiki_fs import WikiFilesystem

AGENT_GUIDE_PATH = "00_Index/AGENT_GUIDE.md"


def load_system_prompt(wiki: WikiFilesystem) -> str:
    """Load AGENT_GUIDE.md and use it as the system prompt."""
    content = wiki.read_file(AGENT_GUIDE_PATH)
    if not content:
        return "Bạn là AI Agent của Innovation Hub. Sử dụng tools để đọc wiki vault và trả lời câu hỏi."

    # Strip YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        content = parts[2].strip() if len(parts) >= 3 else content

    return content
