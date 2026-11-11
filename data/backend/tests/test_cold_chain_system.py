import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.product import Product
from app.models.shipment import Shipment
from app.models.container import Container
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.threshold_policy import ThresholdPolicy
from app.models.excursion import Excursion
from app.services.excursion_engine import ExcursionRuleEngine
from app.validators.data_validator import DataValidator

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True

def test_auth_login_and_roles():
    # Test valid login with seeded admin
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "AdminSecure2026!"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Test me endpoint
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin"
    assert me_resp.json()["role"] == "OT/IT Administrator"

def test_invalid_login():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "WrongPassword!"}
    )
    assert response.status_code == 401

def test_dashboard_metrics():
    # Login as operator
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "operator", "password": "Operator2026!"}
    )
    token = login_resp.json()["access_token"]
    response = client.get(
        "/api/v1/dashboard/metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    metrics = response.json()
    assert "total_shipments" in metrics
    assert "active_excursions" in metrics
    assert metrics["data_validation_success_rate"] >= 80.0

def test_core_entities_get_endpoints():
    endpoints = [
        "/api/v1/products",
        "/api/v1/shipments",
        "/api/v1/containers",
        "/api/v1/sensors",
        "/api/v1/readings",
        "/api/v1/route-stops",
        "/api/v1/threshold-policies",
        "/api/v1/excursions",
        "/api/v1/custody-events",
        "/api/v1/corrective-actions",
        "/api/v1/alerts"
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Failed GET {ep}"
        assert isinstance(resp.json(), list)

def test_excursion_detection_engine():
    # Run excursion evaluation on shipment SHP-2026-000001
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "quality", "password": "Quality2026!"}
    )
    token = login_resp.json()["access_token"]
    resp = client.post(
        "/api/v1/excursions/evaluate/SHP-2026-000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    res = resp.json()
    assert res["shipment_id"] == "SHP-2026-000001"
    repeat = client.post(
        "/api/v1/excursions/evaluate/SHP-2026-000001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert repeat.status_code == 200
    assert repeat.json()["created_excursions"] == 0

def test_duplicate_sensor_reading_is_rejected():
    readings = client.get("/api/v1/readings?limit=1").json()
    assert readings
    reading = readings[0]
    token = client.post("/api/v1/auth/login", data={
        "username": "operator", "password": "Operator2026!"
    }).json()["access_token"]
    response = client.post(
        "/api/v1/readings",
        json=reading,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409

def test_invalid_delivery_order_is_rejected():
    product = client.get("/api/v1/products").json()[0]
    departure = datetime(2026, 1, 2)
    token = client.post("/api/v1/auth/login", data={
        "username": "planner", "password": "Planner2026!"
    }).json()["access_token"]
    response = client.post("/api/v1/shipments", headers={"Authorization": f"Bearer {token}"}, json={
        "shipment_id": "SHP-2026-999999",
        "product_id": product["product_id"],
        "origin": "Origin",
        "destination": "Destination",
        "departure_time": departure.isoformat(),
        "expected_delivery_time": (departure + timedelta(days=2)).isoformat(),
        "actual_delivery_time": (departure - timedelta(hours=1)).isoformat(),
        "shipment_status": "Delivered",
    })
    assert response.status_code == 422

def test_excursion_transitions_preserve_history():
    token = client.post("/api/v1/auth/login", data={
        "username": "quality", "password": "Quality2026!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    open_excursions = client.get("/api/v1/excursions?status=OPEN").json()
    assert open_excursions
    excursion_id = open_excursions[0]["excursion_id"]
    invalid = client.put(f"/api/v1/excursions/{excursion_id}/status", json={"status": "CLOSED"}, headers=headers)
    assert invalid.status_code == 409
    updated = client.put(f"/api/v1/excursions/{excursion_id}/status", json={"status": "ACKNOWLEDGED", "note": "QA review started"}, headers=headers)
    assert updated.status_code == 200
    history = client.get(f"/api/v1/excursions/{excursion_id}/history").json()
    assert history[-1]["from_status"] == "OPEN"
    assert history[-1]["to_status"] == "ACKNOWLEDGED"

def test_data_validator_integrity():
    resp = client.get("/api/v1/validation/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tests"] == 12
    assert data["passed_tests"] >= 4

def test_exports_csv_and_json():
    # CSV export
    csv_resp = client.get("/api/v1/exports/csv/products")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "product_id" in csv_resp.text

    # JSON export
    json_resp = client.get("/api/v1/exports/json/products")
    assert json_resp.status_code == 200
    assert isinstance(json_resp.json(), list)
