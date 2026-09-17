"""Tests for Evidence Scoring and Confidence Calculation."""

import pytest
from backend.app.services.scoring_service import calculate_confidence_score


def test_confidence_scoring_high():
    extracted = {
        "soil": {"organic_carbon": 0.4, "ph": 6.2},
        "climate": {"rainfall": 520.0, "temperature": 29.0},
        "land_use": {"type": "monoculture", "crop": "wheat"},
        "biodiversity": {"species_richness": 12},
        "location": {"latitude": 19.07, "longitude": 73.00}
    }
    evidence = [
        {"document_id": "doc1", "organization": "FAO", "dense_score": 0.88},
        {"document_id": "doc2", "organization": "IPCC", "dense_score": 0.82}
    ]
    conf = calculate_confidence_score(extracted, evidence)
    assert conf.data_completeness == 1.0
    assert conf.overall_score >= 0.78
    assert conf.overall_level == "High"
    assert "FAO" in conf.explanation or "IPCC" in conf.explanation


def test_confidence_scoring_incomplete_data():
    extracted = {
        "soil": {"organic_carbon": 0.3}
    }
    evidence = []
    conf = calculate_confidence_score(extracted, evidence)
    assert conf.data_completeness == 0.2
    assert conf.overall_level in ["Low", "Medium"]
    assert conf.overall_score < 0.78
