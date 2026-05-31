"""Auth middleware tests."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.utils.logger import setup_logging

setup_logging("WARNING")


def test_no_api_key_header_rejected(app_client):
    """Request without X-API-Key header returns 401."""
    resp = app_client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 401


def test_wrong_api_key_rejected(app_client):
    """Request with wrong API key returns 401."""
    resp = app_client.post(
        "/api/chat",
        json={"message": "hello"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_correct_api_key_passes_auth(app_client, auth_headers):
    """Request with correct API key passes auth — verify not 401."""
    with app_client.stream(
        "POST", "/api/chat/stream", json={"message": "hello"}, headers=auth_headers,
    ) as resp:
        assert resp.status_code not in (401, 422)


def test_health_no_auth_required(app_client):
    """/health endpoint works without API key."""
    resp = app_client.get("/health")
    assert resp.status_code == 200


def test_ready_no_auth_required(app_client):
    """/ready endpoint works without API key."""
    resp = app_client.get("/ready")
    assert resp.status_code in (200, 503)


def test_fail_fast_on_missing_api_key(monkeypatch):
    """App startup crashes if AGENT_API_KEY is not set."""
    monkeypatch.delenv("AGENT_API_KEY", raising=False)
    monkeypatch.setenv("MCP_URL", "http://localhost:9999")

    from src.api.app import lifespan
    test_app = FastAPI(lifespan=lifespan)

    with pytest.raises(RuntimeError, match="AGENT_API_KEY"):
        with TestClient(test_app):
            pass
