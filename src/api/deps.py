"""FastAPI dependencies — auth, IP allowlist."""
import os

from fastapi import Header, HTTPException, Request

from src.utils.logger import logger


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Validate X-API-Key header against AGENT_API_KEY env var."""
    expected = os.getenv("AGENT_API_KEY")
    if not expected:
        logger.warning("AGENT_API_KEY not set — rejecting request")
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


async def check_ip_allowlist(request: Request):
    """Optional IP allowlist check via AGENT_ALLOWED_IPS env var."""
    allowed = os.getenv("AGENT_ALLOWED_IPS")
    if not allowed:
        return

    client_ip = request.client.host if request.client else ""
    allowed_ips = [ip.strip() for ip in allowed.split(",") if ip.strip()]

    if client_ip not in allowed_ips:
        logger.warning(f"Rejected request from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="IP not allowed")
