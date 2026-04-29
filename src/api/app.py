"""FastAPI application — REST API for the Innovation Hub Agent."""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.agent.core import create_agent
from src.agent.config import AgentConfig
from src.api.routes.chat import router as chat_router
from src.api.schemas import HealthResponse
from src.utils.logger import logger, setup_logging

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    config = AgentConfig()
    agent, config = create_agent(config)
    app.state.agent = agent
    app.state.config = config
    logger.info(f"Agent started (model={config.model_name})")
    yield


app = FastAPI(
    title="Innovation Hub Agent",
    version="0.1.0",
    description="AI Agent đọc Wiki vault và trả lời câu hỏi",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check."""
    config: AgentConfig = app.state.config
    return HealthResponse(
        status="ok",
        wiki_path=os.getenv("WIKI_PATH", ""),
        model=config.model_name,
    )
