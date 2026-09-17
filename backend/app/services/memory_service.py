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
    """Extracts numeric and categorical environmental variables from natural language text using regex and heuristics."""
    extracted: Dict[str, Any] = {
        "soil": {},
        "climate": {},
        "land_use": {},
        "biodiversity": {},
        "location": {}
    }
    t = text_input.lower()

    # 1. Soil Organic Carbon
    # Matches "organic carbon is 0.3%", "soc = 0.3", "soc 0.4%", "0.3% organic carbon"
    soc_match = re.search(r'(?:organic carbon|soc|carbon content)\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*%', t)
    if not soc_match:
        soc_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:organic carbon|soc)', t)
    if not soc_match:
        soc_match = re.search(r'(?:soc|organic carbon)\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)', t)
    if soc_match:
        try:
            extracted["soil"]["organic_carbon"] = float(soc_match.group(1))
        except ValueError:
            pass

    # 2. Soil pH
    ph_match = re.search(r'(?:ph|soil ph)\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)', t)
    if ph_match:
        try:
            extracted["soil"]["ph"] = float(ph_match.group(1))
        except ValueError:
            pass

    # 3. Soil Moisture
    moisture_match = re.search(r'(?:moisture|soil moisture)\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*%', t)
    if not moisture_match:
        moisture_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:moisture|soil moisture)', t)
    if moisture_match:
        try:
            extracted["soil"]["moisture"] = float(moisture_match.group(1))
        except ValueError:
            pass

    # 4. Rainfall / Precipitation
    # Matches "rainfall is around 500mm", "precip 540 mm", "500mm rainfall"
    rain_match = re.search(r'(?:rainfall|precipitation|rain)\s*(?:is\s+around|is\s+about|is|around|about|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*mm', t)
    if not rain_match:
        rain_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*mm\s*(?:rainfall|rain|precipitation)', t)
    if not rain_match:
        rain_match = re.search(r'(?:rainfall|precipitation|rain)\s*(?:is\s+around|is\s+about|is|around|about|=|:)?\s*([0-9]+(?:\.[0-9]+)?)', t)
    if rain_match:
        try:
            extracted["climate"]["rainfall"] = float(rain_match.group(1))
        except ValueError:
            pass

    # 5. Temperature
    temp_match = re.search(r'(?:temperature|temp)\s*(?:is|=|around|about)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:°c|c|deg|degrees)?', t)
    if temp_match and "rainfall" not in temp_match.group(0):
        try:
            extracted["climate"]["temperature"] = float(temp_match.group(1))
        except ValueError:
            pass

    # 6. Land Use Type & Crop
    if "monoculture" in t:
        extracted["land_use"]["type"] = "monoculture"
    elif "agroforestry" in t:
        extracted["land_use"]["type"] = "agroforestry"
    elif "polyculture" in t or "intercropping" in t or "rotation" in t:
        extracted["land_use"]["type"] = "polyculture"
    elif "fallow" in t:
        extracted["land_use"]["type"] = "fallow"

    for crop in ["wheat", "corn", "maize", "soybean", "rice", "cotton", "barley", "canola", "alfalfa", "sugarcane"]:
        if crop in t:
            extracted["land_use"]["crop"] = crop
            if "type" not in extracted["land_use"]:
                extracted["land_use"]["type"] = "monoculture"
            break

    # 7. Biodiversity (Species Richness)
    rich_match = re.search(r'(?:species richness|richness|species count)\s*(?:is|=|:)?\s*([0-9]+)', t)
    if not rich_match:
        rich_match = re.search(r'([0-9]+)\s*(?:species|taxa)', t)
    if rich_match:
        try:
            extracted["biodiversity"]["species_richness"] = int(rich_match.group(1))
        except ValueError:
            pass

    # 8. Coordinates
    coord_match = re.search(r'lat(?:itude)?\s*[:=]?\s*([0-9.-]+)\s*,\s*lon(?:gitude)?\s*[:=]?\s*([0-9.-]+)', t)
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
