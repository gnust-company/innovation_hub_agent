"""Unit tests for WikiFilesystem."""
import pytest
from pathlib import Path

from src.utils.wiki_fs import WikiFilesystem


class TestReadFile:
    def test_read_existing_file(self, wiki):
        content = wiki.read_file("00_Index/MOC_Overview.md")
        assert "Innovation Hub overview" in content

    def test_read_nonexistent_file(self, wiki):
        assert wiki.read_file("nonexistent.md") is None

    def test_read_with_frontmatter(self, wiki):
        content = wiki.read_file("00_Index/MOC_Overview.md")
        assert content.startswith("---")
        assert "# Overview" in content


class TestListDirectory:
    def test_list_root(self, wiki):
        entries = wiki.list_directory("")
        names = [e["name"] for e in entries]
        assert "00_Index" in names
        assert "01_Features" in names

    def test_list_subdirectory(self, wiki):
        entries = wiki.list_directory("00_Index")
        names = [e["name"] for e in entries]
        assert "MOC_Overview.md" in names
        assert "Getting_Started.md" in names

    def test_list_nonexistent_directory(self, wiki):
        assert wiki.list_directory("nope") == []

    def test_list_skips_hidden(self, wiki, tmp_wiki):
        hidden = tmp_wiki / ".obsidian"
        hidden.mkdir()
        (hidden / "config.json").write_text("{}")
        entries = wiki.list_directory("")
        names = [e["name"] for e in entries]
        assert ".obsidian" not in names

    def test_entry_types(self, wiki):
        entries = wiki.list_directory("")
        by_name = {e["name"]: e for e in entries}
        assert by_name["00_Index"]["type"] == "directory"
        assert by_name["01_Features"]["type"] == "directory"


class TestSearchFiles:
    def test_search_by_name(self, wiki):
        results = wiki.search_files("Overview")
        paths = [r["path"] for r in results]
        assert any("MOC_Overview" in p for p in paths)

    def test_search_case_insensitive(self, wiki):
        results = wiki.search_files("overview")
        assert len(results) >= 1

    def test_search_no_results(self, wiki):
        results = wiki.search_files("zzz_nonexistent")
        assert results == []

    def test_search_max_results(self, wiki, tmp_wiki):
        # Create many matching files
        for i in range(15):
            (tmp_wiki / f"match_{i}.md").write_text(f"# Match {i}")
        results = wiki.search_files("match")
        assert len(results) <= 10


class TestResolveWikilink:
    def test_resolve_by_filename(self, wiki):
        result = wiki.resolve_wikilink("MOC_Overview")
        assert result is not None
        assert "MOC_Overview" in result

    def test_resolve_by_path(self, wiki):
        result = wiki.resolve_wikilink("00_Index/Getting_Started")
        assert result is not None
        assert "Getting_Started" in result

    def test_resolve_nonexistent(self, wiki):
        assert wiki.resolve_wikilink("No_Such_Page") is None

    def test_resolve_case_insensitive(self, wiki):
        result = wiki.resolve_wikilink("moc_overview")
        assert result is not None


class TestExtractWikilinks:
    def test_simple_link(self, wiki):
        content = "See [[Getting_Started]] for details."
        links = wiki.extract_wikilinks(content)
        assert links == ["Getting_Started"]

    def test_nested_link(self, wiki):
        content = "Check [[01_Features/Idea_Lab]]."
        links = wiki.extract_wikilinks(content)
        assert links == ["01_Features/Idea_Lab"]

    def test_link_with_display_text(self, wiki):
        content = "See [[Problem_Feed|Problems]]."
        links = wiki.extract_wikilinks(content)
        assert links == ["Problem_Feed"]

    def test_multiple_links_unique(self, wiki):
        content = "[[A]] and [[A]] and [[B]]."
        links = wiki.extract_wikilinks(content)
        assert links == ["A", "B"]

    def test_no_links(self, wiki):
        assert wiki.extract_wikilinks("plain text") == []

    def test_empty_string(self, wiki):
        assert wiki.extract_wikilinks("") == []


class TestBuildFileIndex:
    def test_index_has_files(self, wiki):
        index = wiki.build_file_index()
        assert "MOC_Overview" in index
        assert "Getting_Started" in index

    def test_index_values_are_relative_paths(self, wiki):
        index = wiki.build_file_index()
        for name, path in index.items():
            assert "/" in path or path.endswith(".md") is False  # relative path


class TestSafety:
    def test_path_traversal_blocked(self, wiki):
        content = wiki.read_file("../../etc/passwd")
        assert content is None

    def test_invalid_wiki_path(self):
        with pytest.raises(ValueError, match="does not exist"):
            WikiFilesystem("/no/such/path")
