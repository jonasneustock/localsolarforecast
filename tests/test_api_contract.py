import json
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_clearsky_contract_keys():
    r = client.get("/clearsky/54.32/10.12/30/0/5?time=60m")
    assert r.status_code == 200
    data = r.json()
    assert "result" in data
    assert "message" in data
    res = data["result"]
    assert set(res.keys()) == {"watts", "watt_hours", "watt_hours_day"}
    # keys should be strings
    if res["watts"]:
        k = next(iter(res["watts"]))
        assert isinstance(k, str)


def test_estimate_same_shape_as_clearsky():
    r1 = client.get("/clearsky/54.32/10.12/30/0/5")
    r2 = client.get("/estimate/54.32/10.12/30/0/5")
    d1 = r1.json()["result"]
    d2 = r2.json()["result"]
    assert set(d1.keys()) == set(d2.keys())


def test_metrics_endpoint_present():
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "http_requests_total" in text
