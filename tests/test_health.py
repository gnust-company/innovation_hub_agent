"""Health and readiness endpoint tests — E.5."""


def test_health_returns_ok(app_client):
    """/health returns expected shape with status ok."""
    resp = app_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model" in data
    assert "wiki_path" in data
    assert "version" in data


def test_health_has_security_headers(app_client):
    """Responses include security headers."""
    resp = app_client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"


def test_ready_when_config_initialized(app_client):
    """/ready returns 200 when config is set and wiki path is valid."""
    resp = app_client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"


def test_ready_when_config_missing(app_client, monkeypatch):
    """/ready returns 503 when config is not initialized."""
    del app_client.app.state.config
    resp = app_client.get("/ready")
    assert resp.status_code == 503
