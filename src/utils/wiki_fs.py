"""Wiki filesystem utility — reads the local wiki vault."""
import os
import re
from pathlib import Path
from typing import Optional


class WikiFilesystem:
    """Low-level file operations on the local wiki vault."""

    def __init__(self, wiki_path: str):
        self.root = Path(wiki_path).resolve()
        if not self.root.is_dir():
            raise ValueError(f"Wiki path does not exist: {self.root}")

    def read_file(self, rel_path: str) -> Optional[str]:
        """Read a file's content. Returns None if not found."""
        target = (self.root / rel_path).resolve()
        if not self._is_safe(target) or not target.is_file():
            return None
        return target.read_text(encoding="utf-8")

    def list_directory(self, rel_path: str = "") -> list[dict]:
        """List files and directories under a path."""
        target = (self.root / rel_path).resolve()
        if not self._is_safe(target) or not target.is_dir():
            return []
        entries = []
        for item in sorted(target.iterdir()):
            if item.name.startswith(".") or item.name == "_overrides":
                continue
            entries.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item.relative_to(self.root)),
            })
        return entries

    def search_files(self, query: str, max_results: int = 10) -> list[dict]:
        """Search wiki files by filename match."""
        query_lower = query.lower()
        results = []
        for md_path in self.root.rglob("*.md"):
            if self._is_hidden(md_path):
                continue
            rel = str(md_path.relative_to(self.root))
            if query_lower in rel.lower():
                results.append({"path": rel, "name": md_path.name})
                if len(results) >= max_results:
                    break
        return results

    def resolve_wikilink(self, link: str) -> Optional[str]:
        """
        Resolve a wikilink to a relative file path.
        Handles:
          - 'Note_Name'           -> fuzzy match by filename
          - 'folder/Note_Name'    -> direct path match
        Returns relative path or None.
        """
        # Already path-qualified? Try direct match
        if "/" in link:
            candidate = (self.root / f"{link}.md").resolve()
            if self._is_safe(candidate) and candidate.is_file():
                return str(candidate.relative_to(self.root))

        # Fallback: match by filename stem
        link_lower = link.lower().replace(" ", "_")
        for md_path in self.root.rglob("*.md"):
            if self._is_hidden(md_path):
                continue
            if md_path.stem.lower() == link_lower:
                return str(md_path.relative_to(self.root))

        return None

    def extract_wikilinks(self, content: str) -> list[str]:
        """Extract all [[WikiLinks]] from markdown content.

        Handles:
          - [[SimpleLink]]
          - [[folder/NestedLink]]
          - [[Link|Display Text]]  (returns only the link part)
        Returns unique, ordered list of link targets.
        """
        raw = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        seen = set()
        result = []
        for link in raw:
            link = link.strip()
            if link and link not in seen:
                seen.add(link)
                result.append(link)
        return result

    def build_file_index(self) -> dict[str, str]:
        """Build a mapping of note_name -> relative_path for fast lookup."""
        index = {}
        for md_path in self.root.rglob("*.md"):
            if self._is_hidden(md_path):
                continue
            rel = str(md_path.relative_to(self.root))
            index[md_path.stem] = rel
        return index

    def _is_safe(self, path: Path) -> bool:
        """Prevent path traversal outside the wiki root."""
        try:
            path.resolve().relative_to(self.root)
            return True
        except ValueError:
            return False

    def _is_hidden(self, path: Path) -> bool:
        """Check if path is inside a hidden directory (e.g. .obsidian)."""
        parts = path.relative_to(self.root).parts
        return any(p.startswith(".") for p in parts)
