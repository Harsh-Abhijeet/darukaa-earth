"""Tests for Agentic LangGraph Workflow Execution."""

import pytest
import uuid
from backend.app.agent.workflow import workflow_engine


def test_agent_workflow_full_pipeline(db_session):
    profile = {
        "location": {"latitude": 19.07, "longitude": 73.00},
        "soil": {"ph": 6.1, "organic_carbon": 0.3, "moisture": 12.0},
        "climate": {"rainfall": 540.0, "temperature": 29.0},
        "land_use": {"type": "monoculture", "crop": "wheat"},
        "biodiversity": {"species_richness": 12}
    }
    initial_state = {
        "conversation_id": str(uuid.uuid4()),
        "user_message": "Run diagnosis.",
        "structured_profile": profile,
        "intent": "analyze",
        "extracted_variables": profile,
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
    output = workflow_engine.run(initial_state, db=db_session)
    assert output["clarification_needed"] is False
    assert "assessment_response" in output
    ass = output["assessment_response"]
    assert len(ass["recommendations"]) > 0
    assert ass["confidence"]["overall_score"] > 0.5
