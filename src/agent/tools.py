"""Wiki tool definitions for the ReAct agent."""
import os
from typing import Optional

from langchain_core.tools import tool

from src.utils.wiki_fs import WikiFilesystem

_wiki: Optional[WikiFilesystem] = None


def _get_wiki() -> WikiFilesystem:
    global _wiki
    if _wiki is None:
        wiki_path = os.getenv("WIKI_PATH")
        if not wiki_path:
            raise ValueError("WIKI_PATH environment variable is not set")
        _wiki = WikiFilesystem(wiki_path)
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
    content = _get_wiki().read_file(path)
    if content is None:
        return f"Error: File not found: {path}"
    return content


@tool
def list_directory(path: str = "") -> str:
    """List all files and directories in a wiki vault directory.

    Args:
        path: Relative directory path (e.g., '03_Events/'). Empty string lists root.
    """
    entries = _get_wiki().list_directory(path)
    if not entries:
        return f"Directory not found or empty: {path or '/'}"
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
    results = _get_wiki().search_files(query)
    if not results:
        return f"No files found matching: {query}"
    lines = [f"{r['path']}" for r in results]
    return "\n".join(lines)


@tool
def resolve_wikilink(link: str) -> str:
    """Convert a wiki link like 'Note_Name' or 'folder/Note_Name' to an actual file path.

    Args:
        link: Wiki link to resolve (e.g., 'JWT_Flow' or '04_Authentication/JWT_Flow')
    """
    resolved = _get_wiki().resolve_wikilink(link)
    if resolved is None:
        return f"Could not resolve wiki link: {link}"
    return resolved
