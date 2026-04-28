"""Wiki tool definitions for the ReAct agent."""
import os
import logging
from typing import Optional

from langchain_core.tools import tool

from src.utils.wiki_fs import WikiFilesystem

logger = logging.getLogger("innovation_hub_agent")

_wiki: Optional[WikiFilesystem] = None


def _get_wiki() -> WikiFilesystem:
    global _wiki
    if _wiki is None:
        wiki_path = os.getenv("WIKI_PATH")
        if not wiki_path:
            raise ValueError("WIKI_PATH environment variable is not set")
        try:
            _wiki = WikiFilesystem(wiki_path)
        except ValueError as e:
            raise ValueError(f"Wiki vault unavailable: {e}")
    return _wiki


def reset_wiki(path: Optional[str] = None):
    """Reset the singleton — used in tests."""
    global _wiki
    if path:
        _wiki = WikiFilesystem(path)
    else:
        _wiki = None


@tool
def read_file(path: str) -> str:
    """Read a file's content from the wiki vault.

    Args:
        path: Relative path to the file (e.g., '00_Index/AGENT_GUIDE.md')
    """
    try:
        wiki = _get_wiki()
    except ValueError as e:
        return f"Error: Wiki vault is unavailable. {e}"

    content = wiki.read_file(path)
    if content is None:
        filename = path.split("/")[-1].replace(".md", "")
        return (
            f"Error: File not found: {path}\n"
            f"Tip: Try `search_wiki('{filename}')` to find the correct path, "
            f"or `list_directory()` to browse available files."
        )

    links = wiki.extract_wikilinks(content)
    if links:
        lines = [f"  → [[{l}]]" for l in links]
        content += "\n\n---\n**Liên kết phát hiện trong file:**\n" + "\n".join(lines)

    return content


@tool
def list_directory(path: str = "") -> str:
    """List all files and directories in a wiki vault directory.

    Args:
        path: Relative directory path (e.g., '03_Events/'). Empty string lists root.
    """
    try:
        wiki = _get_wiki()
    except ValueError as e:
        return f"Error: Wiki vault is unavailable. {e}"

    entries = wiki.list_directory(path)
    if not entries:
        return f"Directory not found or empty: {path or '/'}\nTip: Try `list_directory()` to see root contents."
    lines = []
    for e in entries:
        kind = "DIR " if e["type"] == "directory" else "FILE"
        lines.append(f"{kind}  {e['path']}")
    return "\n".join(lines)


@tool
def search_wiki(query: str) -> str:
    """Search for files in the wiki vault matching a query string.

    Args:
        query: Search term to match against file paths and names.
    """
    try:
        wiki = _get_wiki()
    except ValueError as e:
        return f"Error: Wiki vault is unavailable. {e}"

    results = wiki.search_files(query)
    if not results:
        return (
            f"No files found matching: {query}\n"
            f"Tip: Try a different search term or `list_directory()` to browse."
        )
    lines = [f"{r['path']}" for r in results]
    return "\n".join(lines)


@tool
def resolve_wikilink(link: str) -> str:
    """Convert a wiki link like 'Note_Name' or 'folder/Note_Name' to an actual file path.

    Args:
        link: Wiki link to resolve (e.g., 'JWT_Flow' or '04_Authentication/JWT_Flow')
    """
    try:
        wiki = _get_wiki()
    except ValueError as e:
        return f"Error: Wiki vault is unavailable. {e}"

    resolved = wiki.resolve_wikilink(link)
    if resolved is None:
        return (
            f"Could not resolve wiki link: {link}\n"
            f"Tip: Try `search_wiki('{link}')` to find the correct file."
        )
    return resolved
