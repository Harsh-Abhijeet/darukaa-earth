"""20 Environmental Test Cases for Evaluation Framework conforming to Requirement #21."""

TEST_CASES = [
    {
        "id": "TC_01",
        "name": "Semi-Arid Monoculture Wheat (Low SOC, Low Rainfall, High Temp)",
        "type": "multi_metric_reasoning",
        "input": {
            "location": {"latitude": 19.07, "longitude": 73.00},
            "soil": {"ph": 6.1, "organic_carbon": 0.3, "moisture": 12.0, "bulk_density": 1.48},
            "climate": {"rainfall": 540.0, "temperature": 29.0},
            "land_use": {"type": "monoculture", "crop": "wheat"},
            "biodiversity": {"species_richness": 12}
        },
        "expected_triad": ["soil_organic_carbon", "rainfall", "temperature"],
        "expected_citation_orgs": ["FAO", "IPCC"]
    },
    {
        "id": "TC_02",
        "name": "Acidic Tropical Buffer Deforestation Parcel",
        "type": "multi_metric_reasoning",
        "input": {
            "location": {"latitude": -3.46, "longitude": -62.21},
            "soil": {"ph": 4.6, "organic_carbon": 0.8, "moisture": 28.0},
            "climate": {"rainfall": 1900.0, "temperature": 27.5},
            "land_use": {"type": "pasture", "crop": "brachiaria", "buffer_strip_width_m": 1.5},
            "biodiversity": {"species_richness": 16}
        },
        "expected_triad": ["buffer_strip_width_m", "rainfall", "species_richness"],
        "expected_citation_orgs": ["UNEP", "IPCC"]
    },
    {
        "id": "TC_03",
        "name": "Alkaline Sodic Arid Cotton Farm",
        "type": "multi_metric_reasoning",
        "input": {
            "location": {"latitude": 27.02, "longitude": 71.20},
            "soil": {"ph": 8.5, "organic_carbon": 0.22, "bulk_density": 1.56},
            "climate": {"rainfall": 290.0, "temperature": 33.5},
            "land_use": {"type": "monoculture", "crop": "cotton"},
            "biodiversity": {"species_richness": 7}
        },
        "expected_triad": ["soil_ph", "soil_organic_carbon", "bulk_density"],
        "expected_citation_orgs": ["ISRIC", "FAO"]
    },
    {
        "id": "TC_04",
        "name": "Degraded Steppe Rangeland with Overgrazing",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 6.8, "organic_carbon": 0.45, "moisture": 10.0},
            "climate": {"rainfall": 350.0, "temperature": 22.0},
            "land_use": {"type": "monoculture", "crop": "grazing pasture", "canopy_cover": 2.0},
            "biodiversity": {"species_richness": 9, "habitat_diversity_index": 0.18}
        },
        "expected_triad": ["soil_organic_carbon", "rainfall", "temperature"],
        "expected_citation_orgs": ["FAO", "UNEP"]
    },
    {
        "id": "TC_05",
        "name": "High Chemical Fertilizer Intensive Corn Farm",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 5.8, "organic_carbon": 0.7, "moisture": 18.0},
            "climate": {"rainfall": 800.0, "temperature": 24.0},
            "land_use": {"type": "monoculture", "crop": "corn", "buffer_strip_width_m": 0.0},
            "biodiversity": {"species_richness": 11, "pollinator_abundance": 15.0},
            "human_impact": {"chemical_fertilizer_kg_ha": 230.0, "pesticide_applications_per_year": 5}
        },
        "expected_triad": ["buffer_strip_width_m", "rainfall", "species_richness"],
        "expected_citation_orgs": ["UNEP", "FAO"]
    },
    {
        "id": "TC_06",
        "name": "Monoculture Apple Orchard Pollinator Depletion",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 6.4, "organic_carbon": 1.1, "moisture": 22.0},
            "climate": {"rainfall": 750.0, "temperature": 18.0},
            "land_use": {"type": "monoculture", "crop": "apple", "buffer_strip_width_m": 0.0},
            "biodiversity": {"species_richness": 14, "habitat_diversity_index": 0.20, "pollinator_abundance": 18.0}
        },
        "expected_triad": ["land_use_type", "habitat_diversity_index", "species_richness"],
        "expected_citation_orgs": ["UNEP", "GBIF"]
    },
    {
        "id": "TC_07",
        "name": "Severe Hillside Erosion and Runoff Zone",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 6.2, "organic_carbon": 0.6, "moisture": 14.0},
            "climate": {"rainfall": 1200.0, "temperature": 21.0},
            "land_use": {"type": "monoculture", "crop": "cassava", "buffer_strip_width_m": 0.0},
            "biodiversity": {"species_richness": 16}
        },
        "expected_triad": ["rainfall", "buffer_strip_width_m", "species_richness"],
        "expected_citation_orgs": ["IPCC", "UNEP"]
    },
    {
        "id": "TC_08",
        "name": "Arid Heatwave Zone with Acute Moisture Deficit",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 7.4, "organic_carbon": 0.35, "moisture": 8.0},
            "climate": {"rainfall": 410.0, "temperature": 32.0},
            "land_use": {"type": "monoculture", "crop": "millet"},
            "biodiversity": {"species_richness": 10}
        },
        "expected_triad": ["soil_organic_carbon", "rainfall", "temperature"],
        "expected_citation_orgs": ["FAO", "IPCC"]
    },
    {
        "id": "TC_09",
        "name": "Compacted Clay Plow Pan Cropland",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 5.4, "organic_carbon": 0.8, "bulk_density": 1.62, "clay_fraction": 48.0},
            "climate": {"rainfall": 680.0, "temperature": 20.0},
            "land_use": {"type": "monoculture", "crop": "soybean"},
            "biodiversity": {"species_richness": 15}
        },
        "expected_triad": ["soil_ph", "soil_organic_carbon", "bulk_density"],
        "expected_citation_orgs": ["ISRIC", "FAO"]
    },
    {
        "id": "TC_10",
        "name": "Temperate Diversified Agroforestry Baseline",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 6.8, "organic_carbon": 2.5, "moisture": 25.0},
            "climate": {"rainfall": 950.0, "temperature": 14.0},
            "land_use": {"type": "agroforestry", "crop": "hazelnut and clover sward", "buffer_strip_width_m": 10.0},
            "biodiversity": {"species_richness": 52, "habitat_diversity_index": 0.75}
        },
        "expected_triad": ["soil_health", "water_availability", "vegetative_diversity"],
        "expected_citation_orgs": ["FAO", "UNEP"]
    },
    {
        "id": "TC_11",
        "name": "Urban-Agricultural Fringe Corridors",
        "type": "multi_metric_reasoning",
        "input": {
            "soil": {"ph": 7.1, "organic_carbon": 1.1, "moisture": 17.0},
            "climate": {"rainfall": 650.0, "temperature": 23.0},
            "land_use": {"type": "monoculture", "crop": "vegetables", "buffer_strip_width_m": 1.0},
            "biodiversity": {"species_richness": 13, "habitat_diversity_index": 0.28}
        },
        "expected_triad": ["land_use_type", "habitat_diversity_index", "species_richness"],
        "expected_citation_orgs": ["UNEP", "GBIF"]
    },
    # Multi-turn slot filling tests (TC_12 to TC_15)
    {
        "id": "TC_12",
        "name": "Multi-Turn Slot Filling: Turn 1 (Problem Statement)",
        "type": "conversational_memory",
        "message": "Biodiversity is declining on my farm.",
        "expected_clarification": True,
        "expected_missing": ["soil organic carbon (SOC %)", "annual rainfall (mm)", "land-use type (e.g. monoculture, polyculture, or crop type)"]
    },
    {
        "id": "TC_13",
        "name": "Multi-Turn Slot Filling: Turn 2 (Soil Carbon Provided)",
        "type": "conversational_memory",
        "message": "Organic carbon is 0.3%.",
        "expected_clarification": True,
        "expected_remembered": {"soil": {"organic_carbon": 0.3}},
        "expected_missing": ["annual rainfall (mm)", "land-use type (e.g. monoculture, polyculture, or crop type)"]
    },
    {
        "id": "TC_14",
        "name": "Multi-Turn Slot Filling: Turn 3 (Rainfall Provided)",
        "type": "conversational_memory",
        "message": "Rainfall is around 500mm.",
        "expected_clarification": True,
        "expected_remembered": {"soil": {"organic_carbon": 0.3}, "climate": {"rainfall": 500.0}},
        "expected_missing": ["land-use type (e.g. monoculture, polyculture, or crop type)"]
    },
    {
        "id": "TC_15",
        "name": "Multi-Turn Slot Filling: Turn 4 (Land Use Provided - Triggers Analysis)",
        "type": "conversational_memory",
        "message": "It is monoculture wheat.",
        "expected_clarification": False,
        "expected_missing": [],
        "expected_assessment_generated": True
    },
    # Scientific Integrity & Safeguard Tests
    {
        "id": "TC_16",
        "name": "Hallucination Resistance Test",
        "type": "hallucination_resistance",
        "input": {
            "soil": {"ph": 6.2, "organic_carbon": 0.4, "moisture": 11.0},
            "climate": {"rainfall": 520.0, "temperature": 28.0},
            "land_use": {"type": "monoculture", "crop": "sorghum"},
            "biodiversity": {"species_richness": 10}
        },
        "verify": "no_fabricated_unsupported_numbers"
    },
    {
        "id": "TC_17",
        "name": "Citation Correctness & Metadata Completeness",
        "type": "citation_validation",
        "input": {
            "soil": {"ph": 6.0, "organic_carbon": 0.35},
            "climate": {"rainfall": 550.0, "temperature": 27.0},
            "land_use": {"type": "monoculture", "crop": "barley"}
        },
        "required_metadata_fields": ["source_name", "organization", "year", "page", "topic", "metric"]
    },
    {
        "id": "TC_18",
        "name": "External API Outage Graceful Fallback",
        "type": "fallback_resilience",
        "coordinates": {"latitude": 21.15, "longitude": 79.08},
        "verify": "fallback_label_present"
    },
    {
        "id": "TC_19",
        "name": "Structured JSON Input/Output Schema Conformance",
        "type": "schema_conformance",
        "input": {
            "location": {"latitude": 19.07, "longitude": 73.00},
            "soil": {"ph": 6.1, "organic_carbon": 0.3, "moisture": 12.0},
            "climate": {"rainfall": 540.0, "temperature": 29.0},
            "land_use": {"type": "monoculture", "crop": "wheat"},
            "biodiversity": {"species_richness": 12}
        },
        "required_root_keys": ["assessment", "recommendations", "metrics", "time_horizon", "confidence", "evidence"]
    },
    {
        "id": "TC_20",
        "name": "Multi-Variable Triad Reasoning Requirement Check",
        "type": "triad_constraint",
        "input": {
            "soil": {"organic_carbon": 0.3},
            "climate": {"rainfall": 540.0, "temperature": 29.0},
            "land_use": {"type": "monoculture", "crop": "wheat"}
        },
        "min_variables_analyzed": 3
    }
]
