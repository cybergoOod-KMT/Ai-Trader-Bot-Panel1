from fastapi.testclient import TestClient

from app.main import app
from app.services.script_runner import script_runner_service


def test_health_endpoint_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_metrics_endpoint_returns_prometheus_text() -> None:
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "panel_orders_total" in response.text


def test_script_runner_rejects_path_traversal() -> None:
    try:
        script_runner_service._resolve_script_path("../escape.py")  # noqa: SLF001
    except Exception as exc:  # noqa: BLE001
        assert "outside scripts/trading" in str(exc.detail)  # type: ignore[attr-defined]
    else:
        raise AssertionError("path traversal should fail")
