"""System prompt loader — reads AGENT_GUIDE.md from the wiki vault."""
import os

from src.utils.wiki_fs import WikiFilesystem

AGENT_GUIDE_PATH = "00_Index/AGENT_GUIDE.md"

SYSTEM_PROMPT_TEMPLATE = """You are the Innovation Hub Agent — an AI assistant that answers questions about the Innovation Hub platform.

Your knowledge base is the Obsidian Wiki vault. Follow this reasoning loop:
1. REASON: What wiki files might contain the answer?
2. ACT: Use available tools to read relevant files
3. OBSERVE: Look for [[WikiLinks]] in the content — they point to related pages
4. DECIDE: If more context is needed, follow wiki links and read more files
5. ANSWER: Only answer when you have sufficient context from the wiki

Available tools:
- read_file(path): Read a file from the wiki
- list_directory(path): List files in a wiki directory
- search_wiki(query): Search for files in the wiki
- resolve_wikilink(link): Convert [[Link]] to a file path

{agent_guide}

Answer in the same language the user asks the question. Be concise and cite wiki file paths."""


def load_system_prompt(wiki: WikiFilesystem) -> str:
    """Load system prompt, injecting AGENT_GUIDE.md content if available."""
    guide_content = wiki.read_file(AGENT_GUIDE_PATH)
    if guide_content:
        # Strip YAML frontmatter
        if guide_content.startswith("---"):
            parts = guide_content.split("---", 2)
            guide_content = parts[2].strip() if len(parts) >= 3 else guide_content
        return SYSTEM_PROMPT_TEMPLATE.format(agent_guide=guide_content)
    return SYSTEM_PROMPT_TEMPLATE.format(agent_guide="")
