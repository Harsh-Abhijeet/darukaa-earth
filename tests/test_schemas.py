"""Tests for Pydantic Schema Validation."""

import pytest
from pydantic import ValidationError
from backend.app.schemas.environmental import (
    StructuredEnvironmentalProfile, SoilData, ClimateData, LandUseData, LocationData
)
from backend.app.schemas.recommendations import (
    RecommendationItem, CitationMetadata, ConfidenceBreakdown, EcologicalAssessment, EnvironmentalAssessmentResponse
)


def test_valid_structured_profile():
    profile = StructuredEnvironmentalProfile(
        location=LocationData(latitude=19.07, longitude=73.00),
        soil=SoilData(ph=6.1, organic_carbon=0.3, moisture=12.0),
        climate=ClimateData(rainfall=540.0, temperature=29.0),
        land_use=LandUseData(type="monoculture", crop="wheat")
    )
    assert profile.location.latitude == 19.07
    assert profile.soil.organic_carbon == 0.3
    assert profile.get_completeness_score() >= 0.6


def test_invalid_location_latitude():
    with pytest.raises(ValidationError):
        LocationData(latitude=95.0, longitude=73.00)


def test_recommendation_item_schema():
    citation = CitationMetadata(
        source_name="FAO Soil Biodiversity Report",
        organization="FAO",
        year=2020,
        page="45-78",
        url="https://fao.org",
        topic="Soil Carbon",
        metric="soil_organic_carbon",
        quoted_text="Cover cropping increases SOC by 0.15% to 0.30%."
    )
    item = RecommendationItem(
        recommendation="Plant multi-species cover crops.",
        scientific_reasoning="Increases microbial respiration and water infiltration.",
        impacted_metrics=["soil_organic_carbon", "soil_moisture"],
        expected_impact="Increases SOC by 0.15-0.30% over 3-5 years (FAO 2020).",
        time_horizon="Medium term (1-3 yrs)",
        confidence="High",
        confidence_score=0.88,
        evidence=[citation]
    )
    assert item.confidence == "High"
    assert len(item.evidence) == 1
    assert item.evidence[0].organization == "FAO"
