"""Agentic LangGraph Workflow Definition.

Implements the complete 11-step agentic decision loop conforming to Requirement #10:
START
  -> intent detection
  -> environmental variable extraction
  -> missing-data check
  -> clarification if required -> END (waiting for user turn)
  -> environmental data enrichment
  -> knowledge retrieval
  -> multi-metric reasoning (>= 3 variables)
  -> recommendation generation
  -> evidence validation
       -> [if weak evidence] -> query rewriting -> knowledge retrieval
  -> recommendation formatting
END
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agent.state import AgentState
from backend.app.agent.nodes import (
    intent_detection_node,
    variable_extraction_node,
    missing_data_check_node,
    clarification_node,
    enrichment_node,
    knowledge_retrieval_node,
    multi_metric_reasoning_node,
    recommendation_generation_node,
    evidence_validation_node,
    query_rewriting_node,
    formatting_node
)
from backend.app.core.logging import logger

# Try importing LangGraph if installed in environment
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    END = "__end__"


class EnvironmentalScientistWorkflow:
    """Manages execution of the agentic environmental scientist LangGraph pipeline."""

    def __init__(self):
        self.compiled_graph = None
        if LANGGRAPH_AVAILABLE:
            try:
                self._build_langgraph()
            except Exception as e:
                logger.warning(f"LangGraph initialization deferred: {e}")

    def _build_langgraph(self):
        """Constructs official LangGraph StateGraph with conditional edges."""
        builder = StateGraph(AgentState)

        # Add Nodes
        builder.add_node("intent_detection", intent_detection_node)
        builder.add_node("variable_extraction", variable_extraction_node)
        builder.add_node("missing_data_check", missing_data_check_node)
        builder.add_node("clarification", clarification_node)
        builder.add_node("enrichment", enrichment_node)
        builder.add_node("knowledge_retrieval", knowledge_retrieval_node)
        builder.add_node("multi_metric_reasoning", multi_metric_reasoning_node)
        builder.add_node("recommendation_generation", recommendation_generation_node)
        builder.add_node("evidence_validation", evidence_validation_node)
        builder.add_node("query_rewriting", query_rewriting_node)
        builder.add_node("formatting", formatting_node)

        # Edges
        builder.set_entry_point("intent_detection")
        builder.add_edge("intent_detection", "variable_extraction")
        builder.add_edge("variable_extraction", "missing_data_check")

        # Conditional Edge: Clarification vs Enrichment
        def route_missing(state: AgentState):
            if state.get("clarification_needed", False):
                return "clarification"
            return "enrichment"

        builder.add_conditional_edges("missing_data_check", route_missing, {
            "clarification": "clarification",
            "enrichment": "enrichment"
        })
        builder.add_edge("clarification", END)

        builder.add_edge("enrichment", "knowledge_retrieval")
        builder.add_edge("knowledge_retrieval", "multi_metric_reasoning")
        builder.add_edge("multi_metric_reasoning", "recommendation_generation")
        builder.add_edge("recommendation_generation", "evidence_validation")

        # Conditional Edge: Evidence Validation loop vs Formatting
        def route_validation(state: AgentState):
            if not state.get("validation_passed", True) and state.get("retry_count", 0) < 2:
                return "query_rewriting"
            return "formatting"

        builder.add_conditional_edges("evidence_validation", route_validation, {
            "query_rewriting": "query_rewriting",
            "formatting": "formatting"
        })
        builder.add_edge("query_rewriting", "knowledge_retrieval")
        builder.add_edge("formatting", END)

        self.compiled_graph = builder.compile()

    def run(self, initial_state: AgentState, db: Session) -> Dict[str, Any]:
        """Executes the complete LangGraph workflow deterministically with DB injection."""
        state = dict(initial_state)

        # 1. Intent Detection
        state.update(intent_detection_node(state))

        # 2. Variable Extraction
        state.update(variable_extraction_node(state))

        # 3. Missing Data Check
        state.update(missing_data_check_node(state))

        # 4. Clarification check
        if state.get("clarification_needed"):
            state.update(clarification_node(state))
            return state.get("final_output", {})

        # 5. Environmental Data Enrichment
        state.update(enrichment_node(state, db=db))

        # Loop for retrieval, reasoning, generation, and validation
        max_retries = 2
        for attempt in range(max_retries + 1):
            # 6. Knowledge Retrieval
            state.update(knowledge_retrieval_node(state, db=db))

            # 7. Multi-Metric Reasoning
            state.update(multi_metric_reasoning_node(state))

            # 8. Recommendation Generation
            state.update(recommendation_generation_node(state))

            # 9. Evidence Validation
            state.update(evidence_validation_node(state))

            if state.get("validation_passed", True):
                break
            else:
                # 10. Query Rewriting for secondary retrieval
                state.update(query_rewriting_node(state))

        # 11. Formatting
        state.update(formatting_node(state))
        return state.get("final_output", {})


workflow_engine = EnvironmentalScientistWorkflow()
