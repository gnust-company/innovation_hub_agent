"""Core ReAct agent setup using LangGraph."""
import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from src.agent.prompts import load_system_prompt
from src.agent.tools import read_file, list_directory, search_wiki, resolve_wikilink
from src.utils.wiki_fs import WikiFilesystem

TOOLS = [read_file, list_directory, search_wiki, resolve_wikilink]


def create_agent():
    """Create and return a ReAct agent with wiki tools."""
    # Init wiki filesystem
    wiki_path = os.getenv("WIKI_PATH")
    if not wiki_path:
        raise ValueError("WIKI_PATH environment variable is not set")
    wiki = WikiFilesystem(wiki_path)

    # Load system prompt with AGENT_GUIDE.md
    system_prompt = load_system_prompt(wiki)

    # Setup LLM via NVIDIA NIM (OpenAI-compatible)
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is required. Get one at build.nvidia.com")

    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "moonshotai/kimi-k2.5"),
        api_key=api_key,
        base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        temperature=0,
    )

    # Create ReAct agent
    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=system_prompt,
        checkpointer=MemorySaver(),
    )

    return agent
