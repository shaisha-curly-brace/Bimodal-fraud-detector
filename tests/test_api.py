"""
tests/test_api.py

Integration tests for FastAPI REST API endpoints using TestClient.
Tests all 6 bimodal endpoints and static dashboard mounting.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "healthy")
    assert "models_loaded" in data
    assert "version" in data
    assert "timestamp" in data

    # Test /api/health as well
    resp_api = client.get("/api/health")
    assert resp_api.status_code == 200
    assert resp_api.json()["status"] in ("ok", "healthy")


def test_test_cases_endpoint():
    response = client.get("/api/v1/test-cases")
    assert response.status_code == 200
    data = response.json()
    assert "organic_positive" in data
    assert "organic_negative" in data
    assert "adversarial_mismatch" in data
    assert len(data["organic_positive"]) > 0
    assert len(data["organic_negative"]) > 0
    assert len(data["adversarial_mismatch"]) > 0

    # Test /api/test-cases prefix
    resp_api = client.get("/api/test-cases")
    assert resp_api.status_code == 200


def test_analyze_unified_endpoint():
    payload = {
        "text": "CHASE: Your debit card has been suspended. Verify at http://chase-login-portal.xyz/verify",
        "url": "http://chase-login-portal.xyz/verify"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_tier" in data
    assert "explanation" in data
    assert data["risk_score"] > 60.0
    assert data["contradiction_analysis"]["brand_mismatch_detected"] is True
    assert len(data["explanation"]["evidence_items"]) > 0


def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data or "ablation_benchmark" in data or "message" in data


def test_analyze_text_endpoint():
    payload = {
        "text": "URGENT: Your bank account has been locked. Verify immediately: http://chase-security-check.xyz/login"
    }
    response = client.post("/api/v1/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_tier" in data
    assert "explanation" in data
    assert data["risk_score"] > 60.0
    assert data["url_analysis"]["is_evaluated"] is True
    assert data["url_analysis"]["url"] == "http://chase-security-check.xyz/login"


def test_analyze_text_benign():
    payload = {
        "text": "Hey are we still having dinner at 7pm tonight?"
    }
    response = client.post("/api/v1/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] < 25.0
    assert data["risk_tier"] == "SAFE / LEGITIMATE"
    assert data["url_analysis"]["is_evaluated"] is False


def test_analyze_url_endpoint_phishing():
    payload = {
        "url": "http://194.67.210.15/malware.exe"
    }
    response = client.post("/api/v1/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["url_analysis"]["is_evaluated"] is True
    assert data["risk_score"] > 70.0
    assert data["url_analysis"]["lexical_features"]["IsDomainIP"] == 1


def test_analyze_url_endpoint_legitimate():
    payload = {
        "url": "https://www.chase.com"
    }
    response = client.post("/api/v1/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["url_analysis"]["is_evaluated"] is True
    assert data["risk_score"] < 25.0


def test_analyze_multimodal_endpoint_legitimate():
    payload = {
        "text": "Your CHASE monthly account statement is available.",
        "url": "https://chase.com"
    }
    response = client.post("/api/v1/analyze/multimodal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] < 25.0
    assert data["risk_tier"] == "SAFE / LEGITIMATE"
    assert data["contradiction_analysis"]["brand_mismatch_detected"] is False


def test_analyze_multimodal_endpoint_brand_mismatch():
    payload = {
        "text": "CHASE SECURITY: Unauthorized login attempt detected. Verify your card details now:",
        "url": "http://chase-secure-reactivate.top/verify"
    }
    response = client.post("/api/v1/analyze/multimodal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] > 75.0
    assert data["contradiction_analysis"]["brand_mismatch_detected"] is True
    assert len(data["explanation"]["evidence_items"]) > 0


def test_frontend_index_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "html" in response.headers.get("content-type", "").lower()
