"""LangGraph Agent State definition."""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
import operator


class AgentState(TypedDict):
    conversation_id: str
    user_message: str
    structured_profile: Optional[Dict[str, Any]]
    intent: str  # "analyze", "clarify_reply", "general_query"
    extracted_variables: Dict[str, Any]
    missing_variables: List[str]
    clarification_needed: bool
    clarification_message: Optional[str]
    enriched_data: Dict[str, Any]
    retrieval_query: str
    retrieved_evidence: List[Dict[str, Any]]
    reasoning_signals: List[Dict[str, Any]]
    candidate_recommendations: List[Dict[str, Any]]
    validation_passed: bool
    validation_notes: List[str]
    retry_count: int
    final_output: Optional[Dict[str, Any]]
