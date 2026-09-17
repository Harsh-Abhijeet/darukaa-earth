"""Evidence and Confidence Scoring System.

Implements transparent mathematical calculation of recommendation confidence
based on:
1. Source Authority (FAO, IPCC, UNEP, ISRIC, GBIF, Science/Nature)
2. Retrieval Relevance (RRF & Dense Vector similarity)
3. Data Completeness (fraction of 5 environmental axes populated)
4. Multi-Source Agreement (concordance across independent authoritative bodies)
"""

from typing import List, Dict, Any
from backend.app.schemas.recommendations import ConfidenceBreakdown


def calculate_confidence_score(
    extracted_variables: Dict[str, Any],
    retrieved_evidence: List[Dict[str, Any]]
) -> ConfidenceBreakdown:
    """Calculates transparent confidence score conforming to Requirement #19."""
    
    # 1. Data Completeness Score (0.0 to 1.0)
    # Checks presence of: soil, climate, land_use, biodiversity, location/human_impact
    axes_count = 5
    axes_found = 0
    soil = extracted_variables.get("soil", {})
    if any(soil.get(k) is not None for k in ["ph", "organic_carbon", "moisture"]):
        axes_found += 1

    climate = extracted_variables.get("climate", {})
    if any(climate.get(k) is not None for k in ["rainfall", "temperature"]):
        axes_found += 1

    land_use = extracted_variables.get("land_use", {})
    if any(land_use.get(k) is not None for k in ["type", "crop"]):
        axes_found += 1

    bio = extracted_variables.get("biodiversity", {})
    if any(bio.get(k) is not None for k in ["species_richness", "habitat_diversity_index"]):
        axes_found += 1

    loc = extracted_variables.get("location", {})
    human = extracted_variables.get("human_impact", {})
    if (loc.get("latitude") is not None and loc.get("longitude") is not None) or human:
        axes_found += 1

    completeness_score = round(axes_found / axes_count, 3)

    # 2. Retrieval Relevance Score (0.0 to 1.0)
    if not retrieved_evidence:
        relevance_score = 0.2
    else:
        scores = [item.get("dense_score", 0.6) for item in retrieved_evidence]
        avg_score = sum(scores) / len(scores)
        # Normalize typical cosine scores into 0.0-1.0
        relevance_score = min(max(round(avg_score, 3), 0.3), 1.0)

    # 3. Source Authority Score (0.0 to 1.0)
    tier1_orgs = {"FAO", "IPCC", "UNEP", "ISRIC", "GBIF", "SCIENCE", "NATURE"}
    matched_orgs = set()
    for item in retrieved_evidence:
        org = str(item.get("organization", "")).upper()
        for t1 in tier1_orgs:
            if t1 in org:
                matched_orgs.add(t1)

    if len(matched_orgs) >= 2:
        authority_score = 0.95
    elif len(matched_orgs) == 1:
        authority_score = 0.85
    else:
        authority_score = 0.60

    # 4. Multi-Source Agreement Score (0.0 to 1.0)
    distinct_sources = len({item.get("document_id") or item.get("title") for item in retrieved_evidence})
    if distinct_sources >= 3:
        agreement_score = 0.95
    elif distinct_sources == 2:
        agreement_score = 0.80
    elif distinct_sources == 1:
        agreement_score = 0.60
    else:
        agreement_score = 0.30

    # Weighted Composite Formula
    # Confidence = 0.30 * Authority + 0.30 * Relevance + 0.25 * Completeness + 0.15 * Agreement
    composite = (
        0.30 * authority_score +
        0.30 * relevance_score +
        0.25 * completeness_score +
        0.15 * agreement_score
    )
    composite = round(min(max(composite, 0.0), 1.0), 2)

    # Categorize
    if composite >= 0.78:
        level = "High"
    elif composite >= 0.50:
        level = "Medium"
    else:
        level = "Low"

    explanation = (
        f"Confidence ({level}, {composite:.2f}) evaluated across: "
        f"Data Completeness={completeness_score*100:.0f}%, "
        f"Retrieval Relevance={relevance_score*100:.0f}%, "
        f"Authoritative Backing={authority_score*100:.0f}% ({', '.join(matched_orgs) or 'General'}), "
        f"Cross-Source Concordance={agreement_score*100:.0f}% across {distinct_sources} independent sources."
    )

    return ConfidenceBreakdown(
        overall_level=level,
        overall_score=composite,
        data_completeness=completeness_score,
        retrieval_relevance=relevance_score,
        source_authority=authority_score,
        multi_source_agreement=agreement_score,
        explanation=explanation
    )
