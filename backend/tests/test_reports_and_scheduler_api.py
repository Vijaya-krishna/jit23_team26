from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_active_scheduler():
    response = client.get("/api/scheduler/active")
    assert response.status_code == 200
    data = response.json()
    assert "active_scheduler" in data
    assert "supported_schedulers" in data

def test_get_executive_summary():
    response = client.get("/api/reports/summary")
    assert response.status_code == 200
    data = response.json()
    assert "clock_ticks" in data
    assert "total_energy_kwh" in data
    assert "average_pue" in data
    assert "task_metrics" in data

def test_export_telemetry_csv():
    response = client.get("/api/reports/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Tick,CPU_Util,RAM_Util" in response.text

def test_export_telemetry_json():
    response = client.get("/api/reports/export/json")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "current_telemetry" in data
    assert "telemetry_history" in data
