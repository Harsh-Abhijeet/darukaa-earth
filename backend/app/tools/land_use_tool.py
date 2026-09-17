"""Land-Use and Landscape Fragmentation Diagnostic Tool."""

from typing import Dict, Any, Optional
from backend.app.core.logging import logger


def analyze_land_use_configuration(
    land_use_type: str,
    crop: Optional[str] = None,
    canopy_cover_pct: Optional[float] = None,
    buffer_strip_width_m: Optional[float] = None,
    tillage_practice: Optional[str] = "conventional"
) -> Dict[str, Any]:
    """Evaluates spatial configuration, habitat fragmentation risk, and buffer efficacy.
    
    Conforms to Requirement #4 & #5.
    """
    l_type = (land_use_type or "monoculture").lower()
    
    # 1. Monoculture Vulnerability Index (0.0 - 1.0, higher = more vulnerable)
    if "monoculture" in l_type:
        vulnerability = 0.85
        frag_risk = "High"
    elif "polyculture" in l_type or "rotation" in l_type:
        vulnerability = 0.40
        frag_risk = "Moderate"
    elif "agroforestry" in l_type or "silvopasture" in l_type:
        vulnerability = 0.18
        frag_risk = "Low"
    else:
        vulnerability = 0.50
        frag_risk = "Moderate"

    # Canopy adjustments
    canopy = canopy_cover_pct if canopy_cover_pct is not None else (3.0 if "monoculture" in l_type else 22.0)
    if canopy < 5.0:
        vulnerability = min(vulnerability + 0.10, 1.0)

    # Buffer strip assessment
    buffer_width = buffer_strip_width_m if buffer_strip_width_m is not None else 0.0
    buffer_adequate = buffer_width >= 5.0
    buffer_deficit_m = max(0.0, 5.0 - buffer_width)

    # Soil disturbance multiplier
    tillage = (tillage_practice or "conventional").lower()
    tillage_stress = 0.8 if "conventional" in tillage else 0.25

    return {
        "land_use_type": l_type,
        "primary_crop": crop or "cereal/staple",
        "canopy_cover_pct": canopy,
        "monoculture_vulnerability_index": round(vulnerability, 2),
        "fragmentation_risk": frag_risk,
        "current_buffer_width_m": buffer_width,
        "recommended_min_buffer_m": 6.0,
        "buffer_deficit_m": buffer_deficit_m,
        "tillage_stress_score": tillage_stress,
        "data_source": "UNEP/FAO Landscape Agroecology Framework"
    }
