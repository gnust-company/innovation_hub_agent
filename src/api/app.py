"""FastAPI application — REST API for the Innovation Hub Agent."""
import os
import time
import uuid
from contextlib import asynccontextmanager
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.agent.core import create_agent
from src.agent.config import AgentConfig
from src.api.deps import verify_api_key, check_ip_allowlist
from src.api.routes.chat import router as chat_router
from src.api.schemas import HealthResponse
from src.utils.logger import logger, setup_logging

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

_AGENT_ENV = os.getenv("AGENT_ENV", "development")
_VERSION = "0.2.0"


class SecurityHeadersMiddleware:
    """Add security headers to every response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"x-xss-protection", b"1; mode=block"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RequestLoggingMiddleware:
    """Log every request with method, path, status, duration."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        status_code = 200

        async def send_with_status(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        await self.app(scope, receive, send_with_status)

        duration_ms = (time.time() - start) * 1000
        path = scope.get("path", "")
        method = scope.get("method", "")
        logger.info(f"[{request_id}] {method} {path} → {status_code} ({duration_ms:.0f}ms)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup — fail fast if misconfigured."""
    api_key = os.getenv("AGENT_API_KEY")
    if not api_key:
        raise RuntimeError("AGENT_API_KEY is required — refusing to start unsecured")

    config = AgentConfig()
    agent, config = create_agent(config)
    app.state.agent = agent
    app.state.config = config
    logger.info(f"Agent started (model={config.model_name}, env={_AGENT_ENV})")
    yield


_docs_url = None if _AGENT_ENV == "production" else "/docs"
_redoc_url = None if _AGENT_ENV == "production" else "/redoc"

app = FastAPI(
    title="Innovation Hub Agent",
    version=_VERSION,
    description="Stateless AI Agent — gateway-ready for Hub BE",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# Middleware order: outermost first → RequestLogging → SecurityHeaders → CORS
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS: only if AGENT_CORS_ORIGINS is set (internal services don't need CORS)
_cors_origins = os.getenv("AGENT_CORS_ORIGINS", "")
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(
    chat_router,
    prefix="/api",
    tags=["chat"],
    dependencies=[Depends(verify_api_key), Depends(check_ip_allowlist)],
)


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — no auth required."""
    config: AgentConfig = app.state.config
    return HealthResponse(
        status="ok",
        wiki_path=os.getenv("WIKI_PATH", ""),
        model=config.model_name,
        version=_VERSION,
    )


@app.get("/ready")
async def ready():
    """Readiness check — verifies agent is initialized and wiki is accessible."""
    if not hasattr(app.state, "agent") or app.state.agent is None:
        return JSONResponse(status_code=503, content={"status": "not ready", "error": "Agent not initialized"})

    wiki_path = os.getenv("WIKI_PATH", "")
    if not wiki_path or not os.path.isdir(wiki_path):
        return JSONResponse(status_code=503, content={"status": "not ready", "error": f"Wiki path invalid: {wiki_path}"})

    return {"status": "ready"}
