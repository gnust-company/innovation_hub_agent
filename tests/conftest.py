"""Shared test fixtures."""
import os
import tempfile
import pytest

from src.utils.wiki_fs import WikiFilesystem
from src.agent.tools import reset_wiki


@pytest.fixture
def tmp_wiki(tmp_path):
    """Create a temporary wiki vault with sample files."""
    # Root file
    (tmp_path / "00_Index").mkdir()
    (tmp_path / "00_Index" / "MOC_Overview.md").write_text(
        "---\ntype: moc\n---\n\n# Overview\nInnovation Hub overview.\n\n"
        "See [[Getting_Started]] for setup.\n"
    )
    (tmp_path / "00_Index" / "Getting_Started.md").write_text(
        "# Getting Started\n\nQuick start guide.\n\nRelated: [[MOC_Overview]]\n"
    )

    # Subfolder
    (tmp_path / "01_Features").mkdir()
    (tmp_path / "01_Features" / "Problem_Feed.md").write_text(
        "# Problem Feed\n\nSubmit and discuss problems.\n"
    )
    (tmp_path / "01_Features" / "Idea_Lab.md").write_text(
        "# Idea Lab\n\nBrainstorm rooms.\n\nSee also [[Problem_Feed]].\n"
    )

    return tmp_path


@pytest.fixture
def wiki(tmp_wiki):
    """WikiFilesystem instance pointing at tmp_wiki."""
    return WikiFilesystem(str(tmp_wiki))


@pytest.fixture(autouse=True)
def clean_wiki_singleton():
    """Reset the tool-level wiki singleton between tests."""
    yield
    reset_wiki()
