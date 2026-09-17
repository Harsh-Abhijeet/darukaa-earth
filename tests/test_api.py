"""Tests for FastAPI HTTP Endpoints."""

import pytest


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "service" in data


def test_analyze_endpoint_structured_json(client):
    """Verifies Requirement #12 and #13: Structured JSON input and output."""
    payload = {
        "location": {
            "latitude": 19.07,
            "longitude": 73.00
        },
        "soil": {
            "ph": 6.1,
            "organic_carbon": 0.3,
            "moisture": 12.0
        },
        "climate": {
            "rainfall": 540.0,
            "temperature": 29.0
        },
        "land_use": {
            "type": "monoculture",
            "crop": "wheat"
        },
        "biodiversity": {
            "species_richness": 12
        }
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify root keys conforming strictly to Requirement #13
    assert "assessment" in data
    assert "recommendations" in data
    assert "metrics" in data
    assert "time_horizon" in data
    assert "confidence" in data
    assert "evidence" in data

    recs = data["recommendations"]
    assert len(recs) > 0
    first_rec = recs[0]
    # Verify fields conforming to Requirement #6
    assert "recommendation" in first_rec
    assert "scientific_reasoning" in first_rec
    assert "impacted_metrics" in first_rec
    assert "expected_impact" in first_rec
    assert "time_horizon" in first_rec
    assert "confidence" in first_rec
    assert "evidence" in first_rec


def test_chat_endpoint_clarification(client):
    """Verifies clarification triggered when core input is incomplete."""
    payload = {
        "message": "Biodiversity is declining on my farm."
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["clarification_needed"] is True
    assert len(data["missing_variables"]) > 0


def test_environment_profile_lifecycle(client):
    payload = {
        "location": {"latitude": 12.97, "longitude": 77.59, "region_name": "Bangalore Urban Fringe"},
        "soil": {"ph": 6.5, "organic_carbon": 1.2},
        "climate": {"rainfall": 900.0, "temperature": 24.0}
    }
    post_res = client.post("/environment/profile", json=payload)
    assert post_res.status_code == 200
    profile_id = post_res.json()["profile_id"]

    get_res = client.get(f"/environment/{profile_id}")
    assert get_res.status_code == 200
    assert get_res.json()["profile_id"] == profile_id
    assert get_res.json()["soil"]["ph"] == 6.5


def test_knowledge_search_endpoint(client):
    res = client.get("/knowledge/search", params={"query": "FAO soil organic carbon", "top_k": 2})
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] > 0
    assert len(data["results"]) > 0
