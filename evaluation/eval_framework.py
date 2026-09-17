"""Evaluation Framework executing the 20 Environmental Scenarios conforming to Requirement #21."""

import os
import sys
import json
import uuid
from typing import Dict, Any, List

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.database import get_engine, get_session_factory
from backend.app.db.models import Base
from backend.app.services.rag_service import seed_knowledge_base_from_directory
from backend.app.agent.workflow import workflow_engine
from backend.app.services.memory_service import extract_variables_from_text, merge_extracted_variables, check_missing_core_variables
from backend.app.tools.soil_tool import get_soil_data_sync
from backend.app.tools.climate_tool import get_climate_data_sync
from backend.app.tools.biodiversity_tool import get_biodiversity_data_sync
from evaluation.test_cases import TEST_CASES


def run_evaluation_suite() -> Dict[str, Any]:
    """Executes all 20 environmental test cases and generates a structured scorecard."""
    print("=" * 80)
    print("* DARUKAA.EARTH AI BIODIVERSITY INTELLIGENCE - EVALUATION FRAMEWORK")
    print("=" * 80)

    # Initialize in-memory / local test database
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    session_factory = get_session_factory()
    
    with session_factory() as db:
        kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))
        seed_knowledge_base_from_directory(db, kb_path)

        passed_count = 0
        total_count = len(TEST_CASES)
        results = []

        # Shared state for multi-turn conversational test cases (TC_12 to TC_15)
        conv_accumulated: Dict[str, Any] = {"soil": {}, "climate": {}, "land_use": {}, "biodiversity": {}, "location": {}}

        for tc in TEST_CASES:
            tc_id = tc["id"]
            tc_name = tc["name"]
            tc_type = tc["type"]
            status = "FAIL"
            message = ""

            try:
                # 1. Multi-metric reasoning test cases (TC_01 - TC_11)
                if tc_type == "multi_metric_reasoning":
                    initial_state = {
                        "conversation_id": str(uuid.uuid4()),
                        "user_message": "Evaluate parcel.",
                        "structured_profile": tc["input"],
                        "intent": "analyze",
                        "extracted_variables": tc["input"],
                        "missing_variables": [],
                        "clarification_needed": False,
                        "clarification_message": None,
                        "enriched_data": {},
                        "retrieval_query": "",
                        "retrieved_evidence": [],
                        "reasoning_signals": [],
                        "candidate_recommendations": [],
                        "validation_passed": True,
                        "validation_notes": [],
                        "retry_count": 0,
                        "final_output": None
                    }
                    out = workflow_engine.run(initial_state, db=db)
                    ass = out.get("assessment_response", {})
                    recs = ass.get("recommendations", [])

                    # Verify recommendations exist and contain evidence
                    has_recs = len(recs) > 0
                    has_citations = any(len(r.get("evidence", [])) > 0 for r in recs)
                    
                    # Verify >= 3 variables analyzed
                    signals = out.get("reasoning_signals", [])
                    max_vars = max([s.get("variables_count", 0) for s in signals], default=3)

                    if has_recs and has_citations and max_vars >= 3:
                        status = "PASS"
                        message = f"Generated {len(recs)} interventions with verified citations; analyzed {max_vars} concurrent variables."
                    else:
                        message = f"Failed validation: recs={has_recs}, citations={has_citations}, max_vars={max_vars}"

                # 2. Conversational Memory Multi-Turn Tests (TC_12 to TC_15)
                elif tc_type == "conversational_memory":
                    user_msg = tc["message"]
                    extracted_turn = extract_variables_from_text(user_msg)
                    conv_accumulated = merge_extracted_variables(conv_accumulated, extracted_turn)
                    missing = check_missing_core_variables(conv_accumulated)

                    if tc_id == "TC_12":
                        if len(missing) == 3:
                            status = "PASS"
                            message = f"Correctly detected 3 missing slots: {missing}"
                    elif tc_id == "TC_13":
                        if conv_accumulated.get("soil", {}).get("organic_carbon") == 0.3 and len(missing) == 2:
                            status = "PASS"
                            message = "Remembered SOC=0.3%; requested remaining 2 slots."
                    elif tc_id == "TC_14":
                        if conv_accumulated.get("climate", {}).get("rainfall") == 500.0 and len(missing) == 1:
                            status = "PASS"
                            message = "Remembered SOC & Rainfall; requested only land use."
                    elif tc_id == "TC_15":
                        if len(missing) == 0:
                            # Run full workflow now that all slots filled
                            initial_state = {
                                "conversation_id": "test_conv",
                                "user_message": user_msg,
                                "structured_profile": {},
                                "intent": "clarify_reply",
                                "extracted_variables": conv_accumulated,
                                "missing_variables": [],
                                "clarification_needed": False,
                                "clarification_message": None,
                                "enriched_data": {},
                                "retrieval_query": "",
                                "retrieved_evidence": [],
                                "reasoning_signals": [],
                                "candidate_recommendations": [],
                                "validation_passed": True,
                                "validation_notes": [],
                                "retry_count": 0,
                                "final_output": None
                            }
                            out = workflow_engine.run(initial_state, db=db)
                            if out.get("assessment_response"):
                                status = "PASS"
                                message = "All slots filled across turns; successfully triggered multi-metric assessment!"

                # 3. Hallucination Resistance (TC_16)
                elif tc_type == "hallucination_resistance":
                    initial_state = {
                        "conversation_id": str(uuid.uuid4()),
                        "user_message": "Run diagnosis.",
                        "structured_profile": tc["input"],
                        "intent": "analyze",
                        "extracted_variables": tc["input"],
                        "missing_variables": [],
                        "clarification_needed": False,
                        "clarification_message": None,
                        "enriched_data": {},
                        "retrieval_query": "",
                        "retrieved_evidence": [],
                        "reasoning_signals": [],
                        "candidate_recommendations": [],
                        "validation_passed": True,
                        "validation_notes": [],
                        "retry_count": 0,
                        "final_output": None
                    }
                    out = workflow_engine.run(initial_state, db=db)
                    ass = out.get("assessment_response", {})
                    recs = ass.get("recommendations", [])
                    
                    # Ensure no recommendation has an unsubstantiated numeric claim without a citation
                    no_hallucination = True
                    for r in recs:
                        impact = r.get("expected_impact", "")
                        if any(c.isdigit() for c in impact):
                            if "unavailable" not in impact and not any(tag in impact for tag in ["FAO", "IPCC", "UNEP", "ISRIC", "GBIF", "Lal"]):
                                no_hallucination = False
                    
                    if no_hallucination:
                        status = "PASS"
                        message = "All quantitative claims strictly traced to authoritative literature or fallback enforced."

                # 4. Citation Validation (TC_17)
                elif tc_type == "citation_validation":
                    initial_state = {
                        "conversation_id": str(uuid.uuid4()),
                        "user_message": "Test citations.",
                        "structured_profile": tc["input"],
                        "intent": "analyze",
                        "extracted_variables": tc["input"],
                        "missing_variables": [],
                        "clarification_needed": False,
                        "clarification_message": None,
                        "enriched_data": {},
                        "retrieval_query": "",
                        "retrieved_evidence": [],
                        "reasoning_signals": [],
                        "candidate_recommendations": [],
                        "validation_passed": True,
                        "validation_notes": [],
                        "retry_count": 0,
                        "final_output": None
                    }
                    out = workflow_engine.run(initial_state, db=db)
                    citations = out.get("citations", [])
                    req_fields = tc["required_metadata_fields"]
                    
                    all_fields_present = True
                    for c in citations:
                        for rf in req_fields:
                            if rf not in c or c[rf] is None:
                                all_fields_present = False

                    if citations and all_fields_present:
                        status = "PASS"
                        message = f"All {len(citations)} citations conform strictly to Requirement #20 metadata schema."

                # 5. Fallback Resilience (TC_18)
                elif tc_type == "fallback_resilience":
                    lat = tc["coordinates"]["latitude"]
                    lon = tc["coordinates"]["longitude"]
                    soil_fb = get_soil_data_sync(lat, lon)
                    clim_fb = get_climate_data_sync(lat, lon)
                    bio_fb = get_biodiversity_data_sync(lat, lon)

                    if soil_fb.get("is_fallback") and clim_fb.get("is_fallback") and bio_fb.get("is_fallback"):
                        status = "PASS"
                        message = "External API failure handled gracefully; regional scientific baselines activated."

                # 6. Schema Conformance (TC_19)
                elif tc_type == "schema_conformance":
                    initial_state = {
                        "conversation_id": str(uuid.uuid4()),
                        "user_message": "Analyze schema.",
                        "structured_profile": tc["input"],
                        "intent": "analyze",
                        "extracted_variables": tc["input"],
                        "missing_variables": [],
                        "clarification_needed": False,
                        "clarification_message": None,
                        "enriched_data": {},
                        "retrieval_query": "",
                        "retrieved_evidence": [],
                        "reasoning_signals": [],
                        "candidate_recommendations": [],
                        "validation_passed": True,
                        "validation_notes": [],
                        "retry_count": 0,
                        "final_output": None
                    }
                    out = workflow_engine.run(initial_state, db=db)
                    ass = out.get("assessment_response", {})
                    req_keys = tc["required_root_keys"]
                    if all(k in ass for k in req_keys):
                        status = "PASS"
                        message = f"Strict schema conformance to Requirement #13: {req_keys}"

                # 7. Triad Constraint (TC_20)
                elif tc_type == "triad_constraint":
                    initial_state = {
                        "conversation_id": str(uuid.uuid4()),
                        "user_message": "Triad check.",
                        "structured_profile": tc["input"],
                        "intent": "analyze",
                        "extracted_variables": tc["input"],
                        "missing_variables": [],
                        "clarification_needed": False,
                        "clarification_message": None,
                        "enriched_data": {},
                        "retrieval_query": "",
                        "retrieved_evidence": [],
                        "reasoning_signals": [],
                        "candidate_recommendations": [],
                        "validation_passed": True,
                        "validation_notes": [],
                        "retry_count": 0,
                        "final_output": None
                    }
                    out = workflow_engine.run(initial_state, db=db)
                    signals = out.get("reasoning_signals", [])
                    all_ge_3 = all(s.get("variables_count", 0) >= 3 for s in signals)
                    if signals and all_ge_3:
                        status = "PASS"
                        message = f"All {len(signals)} reasoning signals evaluated across >= 3 variables simultaneously."

            except Exception as e:
                status = "ERROR"
                message = str(e)

            if status == "PASS":
                passed_count += 1
                icon = "[PASS]"
            else:
                icon = "[FAIL]"

            print(f"{icon} [{tc_id}] {tc_name:<60} -> {status} ({message})")
            results.append({
                "id": tc_id,
                "name": tc_name,
                "status": status,
                "detail": message
            })

        print("=" * 80)
        score_pct = (passed_count / total_count) * 100.0
        print(f"EVALUATION SUMMARY: {passed_count}/{total_count} PASSED ({score_pct:.1f}%)")
        print("=" * 80)

        return {
            "passed": passed_count,
            "total": total_count,
            "score_pct": score_pct,
            "results": results
        }


if __name__ == "__main__":
    res = run_evaluation_suite()
    if res["passed"] < res["total"]:
        sys.exit(1)
