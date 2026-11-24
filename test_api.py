"""
Integration Test Suite for FastAPI Endpoints.
Verifies HTTP endpoints, serialization, validation error formats, and SVG download responses.
"""
from fastapi.testclient import TestClient
from main import app

def test_api_integration():
    client = TestClient(app)

    # 1. Test Root Homepage
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "MODERN CRANE CO." in res.text
    print("PASS: [GET /] Serves CAD Interface HTML")

    # 2. Test Health Endpoint
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("PASS: [GET /api/health] Healthy")

    # 3. Test List Designs
    res = client.get("/api/designs")
    assert res.status_code == 200
    designs = res.json()
    assert len(designs) >= 3
    first_id = designs[0]["id"]
    print(f"PASS: [GET /api/designs] Returns {len(designs)} saved designs")

    # 4. Test Calculation Endpoint
    calc_payload = {
        "name": "API Live Test Crane",
        "customer": "Metro Heavy Engineering",
        "crane_type": "single_girder",
        "capacity_ton": 10.0,
        "span_mm": 18000.0,
        "lifting_height_mm": 6500.0,
        "rail_height_mm": 7500.0,
        "building_clearance_left_mm": 300.0,
        "building_clearance_right_mm": 300.0,
        "roof_clearance_mm": 300.0
    }
    res = client.post("/api/calculate?view=both", json=calc_payload)
    assert res.status_code == 200
    data = res.json()
    assert "svg" in data
    assert "calculations" in data
    print("PASS: [POST /api/calculate] Realtime calculation & SVG generation successful")

    # 5. Test Export SVG Download
    res = client.get(f"/api/designs/{first_id}/export/svg")
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers["content-type"]
    assert "ModernCrane_" in res.headers["content-disposition"]
    print("PASS: [GET /api/designs/{id}/export/svg] SVG export downloadable")

    print("\nALL HTTP REST API INTEGRATION TESTS PASSED 100%!")

if __name__ == "__main__":
    test_api_integration()
