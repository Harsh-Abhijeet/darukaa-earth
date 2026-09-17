"""Pydantic schemas for multi-turn conversational intelligence."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.environmental import StructuredEnvironmentalProfile
from backend.app.schemas.recommendations import EnvironmentalAssessmentResponse, CitationMetadata


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or follow-up response")
    conversation_id: Optional[str] = Field(None, description="Active multi-turn session ID")
    structured_profile: Optional[StructuredEnvironmentalProfile] = Field(
        None, description="Optional structured profile accompanying the message"
    )


class ChatResponse(BaseModel):
    conversation_id: str = Field(..., description="Session ID for multi-turn continuity")
    reply: str = Field(..., description="Environmental scientist agent response")
    clarification_needed: bool = Field(False, description="True if core variables are missing and requested")
    missing_variables: List[str] = Field(default_factory=list, description="List of absent environmental variables")
    accumulated_variables: Dict[str, Any] = Field(default_factory=dict, description="Variables remembered across turns")
    assessment_response: Optional[EnvironmentalAssessmentResponse] = Field(
        None, description="Populated when sufficient variables exist to run scientific analysis"
    )
    citations: List[CitationMetadata] = Field(default_factory=list)
