"""Tests for Multi-Metric Reasoning Engine and Environmental Relationship Ontology."""

import pytest
from backend.app.agent.reasoning_rules import evaluate_multi_metric_rules


def test_arid_triad_reasoning():
    """Tests simultaneous evaluation of SOC + Rainfall + Temperature."""
    variables = {
        "soil": {"organic_carbon": 0.3, "moisture": 10.0},
        "climate": {"rainfall": 500.0, "temperature": 30.0},
        "land_use": {"type": "monoculture", "crop": "wheat"}
    }
    signals = evaluate_multi_metric_rules(variables)
    assert len(signals) >= 1
    
    arid_signal = next((s for s in signals if "Compound Arid Soil-Moisture" in s.name), None)
    assert arid_signal is not None
    assert arid_signal.variables_analyzed == ["soil_organic_carbon", "rainfall", "temperature"]
    assert len(arid_signal.variables_analyzed) >= 3
    assert arid_signal.severity == "High"


def test_monoculture_biodiversity_triad():
    """Tests evaluation of Land Use + Habitat Diversity + Species Richness."""
    variables = {
        "land_use": {"type": "monoculture", "crop": "soybean"},
        "biodiversity": {"species_richness": 10, "habitat_diversity_index": 0.20}
    }
    signals = evaluate_multi_metric_rules(variables)
    mono_signal = next((s for s in signals if "Monoculture Floral Resource Desert" in s.name), None)
    assert mono_signal is not None
    assert len(mono_signal.variables_analyzed) >= 3


def test_no_single_variable_reasoning():
    """Guarantees requirement #5: system must reason across at least three variables simultaneously."""
    test_profiles = [
        {"soil": {"organic_carbon": 0.4}, "climate": {"rainfall": 480.0, "temperature": 31.0}},
        {"land_use": {"type": "monoculture"}, "biodiversity": {"species_richness": 12, "habitat_diversity_index": 0.25}},
        {"soil": {"ph": 4.8, "organic_carbon": 0.7, "bulk_density": 1.55}}
    ]
    for p in test_profiles:
        signals = evaluate_multi_metric_rules(p)
        for sig in signals:
            assert len(sig.variables_analyzed) >= 3, f"Signal {sig.name} only evaluated {len(sig.variables_analyzed)} variables!"
