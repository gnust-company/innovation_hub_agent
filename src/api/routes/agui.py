"""AG-UI endpoint for CopilotKit — exposes LangGraph agent via AG-UI protocol."""
from fastapi import FastAPI

from ag_ui_langgraph import add_langgraph_fastapi_endpoint, LangGraphAgent

from src.agent.core import get_agui_graph
from src.utils.logger import logger


def mount_agui_endpoint(app: FastAPI, prefix: str = "/agui"):
    """Mount AG-UI endpoint onto the FastAPI app.

    This is called after init_mcp() has built the graph.
    Uses a sub-app so the AG-UI endpoint is isolated from auth middleware.
    """
    graph = get_agui_graph()

    agui_app = FastAPI(title="AG-UI Endpoint", docs_url=None, redoc_url=None)

    add_langgraph_fastapi_endpoint(
        app=agui_app,
        agent=LangGraphAgent(
            name="innovation_hub_agent",
            description="Innovation Hub AI Agent — wiki knowledge + platform tools",
            graph=graph,
        ),
        path="/",
    )

    app.mount(prefix, agui_app)
    logger.info("AG-UI endpoint mounted at %s", prefix)
