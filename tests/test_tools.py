"""Tests for Environmental Data Tools and Fallback Behavior."""

import pytest
from backend.app.tools.soil_tool import get_soil_data_sync
from backend.app.tools.climate_tool import get_climate_data_sync
from backend.app.tools.biodiversity_tool import get_biodiversity_data_sync
from backend.app.tools.land_use_tool import analyze_land_use_configuration


def test_soil_tool_fallback():
    data = get_soil_data_sync(latitude=19.07, longitude=73.00)
    assert "ph" in data
    assert "organic_carbon" in data
    assert data["is_fallback"] is True
    assert "ISRIC" in data["data_source"]


def test_climate_tool_fallback():
    data = get_climate_data_sync(latitude=19.07, longitude=73.00)
    assert "rainfall" in data
    assert "temperature" in data
    assert data["is_fallback"] is True
    assert "NASA" in data["data_source"]


def test_biodiversity_tool_fallback():
    data = get_biodiversity_data_sync(latitude=19.07, longitude=73.00)
    assert "species_richness" in data
    assert data["is_fallback"] is True
    assert "GBIF" in data["data_source"]


def test_land_use_analysis():
    res = analyze_land_use_configuration(
        land_use_type="monoculture",
        crop="wheat",
        buffer_strip_width_m=2.0
    )
    assert res["fragmentation_risk"] == "High"
    assert res["buffer_deficit_m"] == 3.0
    assert res["monoculture_vulnerability_index"] >= 0.8
