"""Multi-Turn Conversation Memory and Slot-Filling Service.

Maintains persistent conversation state, extracts environmental variables from
unstructured dialogue, accumulates data across turns, and isolates remaining missing slots.
Conforms to Requirements #3 and #17.
"""

import re
import json
import uuid
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.db.models import Conversation, Message, EnvironmentalProfile, SoilMetrics, ClimateMetrics, LandUseMetrics, BiodiversityMetrics
from backend.app.core.logging import logger


CORE_VARIABLES = [
    ("soil", "organic_carbon", "soil organic carbon (SOC %)"),
    ("climate", "rainfall", "annual rainfall (mm)"),
    ("land_use", "type", "land-use type (e.g., monoculture, polyculture, agroforestry)")
]


def extract_variables_from_text(text_input: str) -> Dict[str, Any]:
    """Extract environmental variables from natural-language text.

    Supports multiple natural-language patterns for numeric and categorical
    environmental variables while preserving the existing nested schema.
    """
    extracted: Dict[str, Any] = {
        "soil": {},
        "climate": {},
        "land_use": {},
        "biodiversity": {},
        "location": {}
    }

    t = text_input.lower()

    # ---------------------------------------------------------
    # 1. Soil Organic Carbon (SOC)
    # ---------------------------------------------------------
    soc_patterns = [
        r'(?:soil\s+organic\s+carbon|organic\s+carbon|soc|carbon\s+content)'
        r'\s*(?:is|=|:|of|at)?\s*([0-9]+(?:\.[0-9]+)?)\s*%',

        r'([0-9]+(?:\.[0-9]+)?)\s*%\s*'
        r'(?:soil\s+organic\s+carbon|organic\s+carbon|soc|carbon\s+content)'
    ]

    for pattern in soc_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["soil"]["organic_carbon"] = float(match.group(1))
                break
            except ValueError:
                pass

    # ---------------------------------------------------------
    # 2. Soil pH
    # ---------------------------------------------------------
    ph_patterns = [
        r'(?:soil\s+ph|ph)\s*(?:is|=|:|of|at)?\s*([0-9]+(?:\.[0-9]+)?)',
        r'ph\s+value\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)'
    ]

    for pattern in ph_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["soil"]["ph"] = float(match.group(1))
                break
            except ValueError:
                pass

    # ---------------------------------------------------------
    # 3. Soil Moisture
    # ---------------------------------------------------------
    moisture_patterns = [
        r'(?:soil\s+moisture|moisture)\s*'
        r'(?:is|=|:|of|at)?\s*([0-9]+(?:\.[0-9]+)?)\s*%',

        r'([0-9]+(?:\.[0-9]+)?)\s*%\s*'
        r'(?:soil\s+moisture|moisture)'
    ]

    for pattern in moisture_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["soil"]["moisture"] = float(match.group(1))
                break
            except ValueError:
                pass

    # ---------------------------------------------------------
    # 4. Rainfall / Precipitation
    # ---------------------------------------------------------
    rain_patterns = [
        # "rainfall is around 500mm"
        # "annual rainfall is about 540 mm"
        # "rainfall of 500 mm"
        # "rainfall around 500 mm"
        r'(?:annual\s+)?(?:rainfall|precipitation|rain)'
        r'\s*(?:(?:is\s+)?(?:around|about)|is|=|:|of)?\s*'
        r'([0-9]+(?:\.[0-9]+)?)\s*mm',

        # "500mm rainfall"
        # "540 mm annual rainfall"
        r'([0-9]+(?:\.[0-9]+)?)\s*mm\s*'
        r'(?:annual\s+)?(?:rainfall|precipitation|rain)',

        # "annual rainfall 540"
        # "rainfall is 540"
        r'(?:annual\s+rainfall|annual\s+precipitation|rainfall|precipitation|rain)'
        r'\s*(?:(?:is\s+)?(?:around|about)|is|=|:|of)?\s*'
        r'([0-9]+(?:\.[0-9]+)?)'
    ]

    for pattern in rain_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["climate"]["rainfall"] = float(match.group(1))
                break
            except ValueError:
                pass
    # ---------------------------------------------------------
    # 5. Temperature
    # ---------------------------------------------------------
    temp_patterns = [
        r'(?:mean\s+surface\s+temperature|average\s+temperature|'
        r'mean\s+temperature|temperature|temp)'
        r'\s*(?:is|=|:|around|about|of|at)?\s*'
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:°c|degrees?\s*c|c)?',

        r'([0-9]+(?:\.[0-9]+)?)\s*°c\s*'
        r'(?:average\s+|mean\s+)?temperature',

        r'([0-9]+(?:\.[0-9]+)?)\s*degrees?\s*c'
    ]

    for pattern in temp_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["climate"]["temperature"] = float(match.group(1))
                break
            except ValueError:
                pass

    # ---------------------------------------------------------
    # 6. Land Use Type
    # ---------------------------------------------------------
    if "monoculture" in t or "mono-culture" in t:
        extracted["land_use"]["type"] = "monoculture"

    elif "agroforestry" in t:
        extracted["land_use"]["type"] = "agroforestry"

    elif (
        "polyculture" in t
        or "poly-culture" in t
        or "intercropping" in t
        or "inter-cropping" in t
        or "crop rotation" in t
        or "rotation" in t
    ):
        extracted["land_use"]["type"] = "polyculture"

    elif "fallow" in t:
        extracted["land_use"]["type"] = "fallow"

    elif "pasture" in t:
        extracted["land_use"]["type"] = "pasture"

    # ---------------------------------------------------------
    # 7. Crop
    # ---------------------------------------------------------
    crop_names = [
        "wheat",
        "corn",
        "maize",
        "soybean",
        "rice",
        "cotton",
        "barley",
        "canola",
        "alfalfa",
        "sugarcane",
        "brachiaria grass",
        "brachiaria"
    ]

    for crop in crop_names:
        if crop in t:
            extracted["land_use"]["crop"] = crop

            # If crop is mentioned but no land-use type is given,
            # preserve the original behavior of treating it as monoculture.
            if "type" not in extracted["land_use"]:
                extracted["land_use"]["type"] = "monoculture"

            break

    # ---------------------------------------------------------
    # 8. Buffer Strip Width
    # ---------------------------------------------------------
    buffer_patterns = [
        r'(?:buffer\s+strip|field\s+buffer|buffer)'
        r'\s*(?:width)?\s*(?:is|=|:|of|at)?\s*'
        r'([0-9]+(?:\.[0-9]+)?)\s*m',

        r'([0-9]+(?:\.[0-9]+)?)\s*m\s*'
        r'(?:buffer\s+strip|field\s+buffer|buffer)'
    ]

    for pattern in buffer_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["land_use"]["buffer_strip_width_m"] = float(match.group(1))
                break
            except ValueError:
                pass

    # Handle phrases such as "no field buffer" / "no buffer"
    if (
        "no field buffer" in t
        or "no buffer strip" in t
        or "no buffer" in t
        or "without a buffer" in t
        or "without buffer" in t
    ):
        extracted["land_use"]["buffer_strip_width_m"] = 0.0

    # ---------------------------------------------------------
    # 9. Biodiversity - Species Richness
    # ---------------------------------------------------------
    richness_patterns = [
        r'(?:species\s+richness|species\s+count|richness)'
        r'\s*(?:is|=|:|of)?\s*([0-9]+)',

        r'([0-9]+)\s*(?:observed\s+)?species\b'
    ]

    for pattern in richness_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["biodiversity"]["species_richness"] = int(match.group(1))
                break
            except ValueError:
                pass

    # ---------------------------------------------------------
    # 10. Habitat Diversity Index
    # ---------------------------------------------------------
    habitat_patterns = [
        r'(?:habitat\s+diversity|habitat\s+diversity\s+index)'
        r'\s*(?:is|=|:|of)?\s*([0-9]+(?:\.[0-9]+)?)',

        r'(?:diversity\s+index)'
        r'\s*(?:is|=|:|of)?\s*([0-9]+(?:\.[0-9]+)?)'
    ]

    for pattern in habitat_patterns:
        match = re.search(pattern, t)
        if match:
            try:
                extracted["biodiversity"]["habitat_diversity_index"] = float(match.group(1))
                break
            except ValueError:
                pass

    # ---------------------------------------------------------
    # 11. Coordinates
    # ---------------------------------------------------------
    coord_match = re.search(
        r'lat(?:itude)?\s*[:=]?\s*([0-9.-]+)'
        r'\s*,\s*'
        r'lon(?:gitude)?\s*[:=]?\s*([0-9.-]+)',
        t
    )

    if coord_match:
        try:
            extracted["location"]["latitude"] = float(coord_match.group(1))
            extracted["location"]["longitude"] = float(coord_match.group(2))
        except ValueError:
            pass

    return extracted

def merge_extracted_variables(base_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges newly discovered variables into existing profile state."""
    merged = dict(base_dict or {})
    for section, values in (new_dict or {}).items():
        if not values:
            continue
        if section not in merged:
            merged[section] = {}
        for k, v in values.items():
            if v is not None:
                merged[section][k] = v
    return merged


def get_or_create_conversation(db: Session, conversation_id: Optional[str] = None) -> Tuple[Conversation, Dict[str, Any]]:
    """Retrieves conversation from database or instantiates new session."""
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            # Reconstruct accumulated state from historical messages
            accumulated: Dict[str, Any] = {"soil": {}, "climate": {}, "land_use": {}, "biodiversity": {}, "location": {}}
            for msg in conv.messages:
                if msg.extracted_state_json:
                    try:
                        state_snapshot = json.loads(msg.extracted_state_json)
                        accumulated = merge_extracted_variables(accumulated, state_snapshot)
                    except Exception:
                        pass
            return conv, accumulated

    new_id = conversation_id or str(uuid.uuid4())
    conv = Conversation(id=new_id, title="Environmental Intelligence Session")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv, {"soil": {}, "climate": {}, "land_use": {}, "biodiversity": {}, "location": {}}


def check_missing_core_variables(variables: Dict[str, Any]) -> List[str]:
    """Identifies which core variables are missing to trigger clarification.
    
    Conforms to Requirement #17:
    Turn 1: Biodiversity declining -> Missing: SOC, rainfall, land use
    Turn 2: SOC=0.3% -> Missing: rainfall, land use
    Turn 3: Rainfall=500mm -> Missing: land use
    """
    missing = []
    soil = variables.get("soil", {})
    if soil.get("organic_carbon") is None and soil.get("ph") is None:
        missing.append("soil organic carbon (SOC %)")

    climate = variables.get("climate", {})
    if climate.get("rainfall") is None:
        missing.append("annual rainfall (mm)")

    land_use = variables.get("land_use", {})
    if not land_use.get("type") and not land_use.get("crop"):
        missing.append("land-use type (e.g. monoculture, polyculture, or crop type)")

    return missing


def save_conversation_turn(
    db: Session,
    conversation_id: str,
    user_text: str,
    reply_text: str,
    extracted_state: Dict[str, Any],
    clarification_requested: bool
):
    """Persists both user query and assistant response with extracted state snapshot."""
    user_msg_id = str(uuid.uuid4())
    bot_msg_id = str(uuid.uuid4())

    user_msg = Message(
        id=user_msg_id,
        conversation_id=conversation_id,
        sender="user",
        content=user_text,
        extracted_state_json=json.dumps(extracted_state)
    )
    db.add(user_msg)

    bot_msg = Message(
        id=bot_msg_id,
        conversation_id=conversation_id,
        sender="assistant",
        content=reply_text,
        clarification_requested=clarification_requested
    )
    db.add(bot_msg)
    db.commit()
