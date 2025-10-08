from fastapi.testclient import TestClient

from app.core import config
from app.main import create_app


def test_rate_limit_429():
    # tighten limit for the test
    config.settings.rate_limit_per_minute = 2
    app = create_app()
    client = TestClient(app)
    # First two allowed
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    # Third should be limited
    r = client.get("/health")
    assert r.status_code == 429
    assert r.json()["message"]["type"] == "error"

