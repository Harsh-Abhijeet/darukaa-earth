"""Tests for Conversational Memory and Progressive Slot Filling conforming to Requirement #17."""

import pytest
from backend.app.services.memory_service import (
    extract_variables_from_text,
    merge_extracted_variables,
    check_missing_core_variables
)


def test_turn1_missing_slots():
    """Turn 1: User says biodiversity is declining."""
    t1 = "Biodiversity is declining on my farm."
    extracted = extract_variables_from_text(t1)
    missing = check_missing_core_variables(extracted)
    assert "soil organic carbon (SOC %)" in missing
    assert "annual rainfall (mm)" in missing
    assert "land-use type (e.g. monoculture, polyculture, or crop type)" in missing


def test_turn2_slot_accumulation():
    """Turn 2: User provides organic carbon."""
    state = {"soil": {}, "climate": {}, "land_use": {}}
    t2 = "Organic carbon is 0.3%."
    new_vars = extract_variables_from_text(t2)
    state = merge_extracted_variables(state, new_vars)
    assert state["soil"]["organic_carbon"] == 0.3

    missing = check_missing_core_variables(state)
    assert "soil organic carbon (SOC %)" not in missing
    assert "annual rainfall (mm)" in missing
    assert "land-use type (e.g. monoculture, polyculture, or crop type)" in missing


def test_turn3_rainfall_accumulation():
    """Turn 3: User provides rainfall."""
    state = {"soil": {"organic_carbon": 0.3}, "climate": {}, "land_use": {}}
    t3 = "Rainfall is around 500mm."
    new_vars = extract_variables_from_text(t3)
    state = merge_extracted_variables(state, new_vars)
    assert state["climate"]["rainfall"] == 500.0

    missing = check_missing_core_variables(state)
    assert len(missing) == 1
    assert "land-use type" in missing[0]


def test_turn4_all_slots_filled():
    """Turn 4: User provides land use -> No missing slots."""
    state = {
        "soil": {"organic_carbon": 0.3},
        "climate": {"rainfall": 500.0},
        "land_use": {}
    }
    t4 = "It is monoculture wheat."
    new_vars = extract_variables_from_text(t4)
    state = merge_extracted_variables(state, new_vars)
    assert state["land_use"]["type"] == "monoculture"
    assert state["land_use"]["crop"] == "wheat"

    missing = check_missing_core_variables(state)
    assert len(missing) == 0
