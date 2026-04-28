"""Unit tests for agent tools."""
import os
import pytest

from src.agent.tools import read_file, list_directory, search_wiki, resolve_wikilink, reset_wiki


@pytest.fixture
def setup_wiki_env(tmp_wiki, monkeypatch):
    """Point tools at tmp_wiki via env var."""
    monkeypatch.setenv("WIKI_PATH", str(tmp_wiki))
    reset_wiki(str(tmp_wiki))


class TestReadFile:
    def test_read_existing(self, setup_wiki_env):
        result = read_file.invoke({"path": "00_Index/MOC_Overview.md"})
        assert "Innovation Hub overview" in result
        assert "Liên kết phát hiện trong file" in result
        assert "Getting_Started" in result

    def test_read_not_found(self, setup_wiki_env):
        result = read_file.invoke({"path": "nonexistent.md"})
        assert "File not found" in result
        assert "Tip" in result

    def test_read_file_with_links(self, setup_wiki_env):
        result = read_file.invoke({"path": "01_Features/Idea_Lab.md"})
        assert "Problem_Feed" in result


class TestListDirectory:
    def test_list_root(self, setup_wiki_env):
        result = list_directory.invoke({"path": ""})
        assert "00_Index" in result
        assert "01_Features" in result

    def test_list_subdirectory(self, setup_wiki_env):
        result = list_directory.invoke({"path": "00_Index"})
        assert "MOC_Overview.md" in result

    def test_list_not_found(self, setup_wiki_env):
        result = list_directory.invoke({"path": "nope"})
        assert "not found" in result


class TestSearchWiki:
    def test_search_match(self, setup_wiki_env):
        result = search_wiki.invoke({"query": "Overview"})
        assert "MOC_Overview" in result

    def test_search_no_match(self, setup_wiki_env):
        result = search_wiki.invoke({"query": "zzz_nonexistent"})
        assert "No files found" in result
        assert "Tip" in result


class TestResolveWikilink:
    def test_resolve_by_name(self, setup_wiki_env):
        result = resolve_wikilink.invoke({"link": "MOC_Overview"})
        assert "MOC_Overview" in result

    def test_resolve_by_path(self, setup_wiki_env):
        result = resolve_wikilink.invoke({"link": "00_Index/Getting_Started"})
        assert "Getting_Started" in result

    def test_resolve_not_found(self, setup_wiki_env):
        result = resolve_wikilink.invoke({"link": "No_Such_Page"})
        assert "Could not resolve" in result
        assert "Tip" in result


class TestWikiUnavailable:
    def test_read_file_wiki_unavailable(self, monkeypatch):
        monkeypatch.setenv("WIKI_PATH", "/no/such/path")
        reset_wiki()
        # Set to invalid path and reset singleton
        from src.agent import tools
        tools._wiki = None
        monkeypatch.setenv("WIKI_PATH", "/no/such/path")
        result = read_file.invoke({"path": "anything.md"})
        assert "Wiki vault is unavailable" in result or "Error" in result
