"""Pydantic schemas for scientific recommendations, evidence citations, and assessment responses.

Strictly adheres to Requirements #6, #7, #13, and #20.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CitationMetadata(BaseModel):
    """Citation metadata conforming strictly to Requirement #20."""
    source_name: str = Field(..., description="Authoritative publication, report, or dataset name")
    organization: str = Field(..., description="Issuing entity (e.g. FAO, IPCC, UNEP, ISRIC, GBIF)")
    year: int = Field(..., description="Publication year")
    page: Optional[str] = Field(None, description="Page number or section")
    url: Optional[str] = Field(None, description="Direct URL or DOI link")
    topic: Optional[str] = Field(None, description="Scientific subject domain")
    metric: Optional[str] = Field(None, description="Specific environmental metric covered")
    quoted_text: Optional[str] = Field(None, description="Verbatim evidentiary quote")


class RecommendationItem(BaseModel):
    """Recommendation item strictly adhering to Requirement #6 & #7."""
    recommendation: str = Field(..., description="What should the user do?")
    scientific_reasoning: str = Field(..., description="Why should this intervention work?")
    impacted_metrics: List[str] = Field(..., description="Which environmental metrics are expected to change?")
    expected_impact: str = Field(
        ...,
        description="Measurable estimate supported by evidence, or explicitly stating quantitative estimate is unavailable."
    )
    time_horizon: str = Field(..., description="Short term (<1 yr), Medium term (1-3 yrs), or Long term (>3 yrs)")
    confidence: str = Field(..., description="High, Medium, or Low")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Numerical confidence metric 0.0 - 1.0")
    evidence: List[CitationMetadata] = Field(default_factory=list, description="Authoritative scientific citations")


class ConfidenceBreakdown(BaseModel):
    overall_level: str = Field(..., description="High, Medium, or Low")
    overall_score: float = Field(..., ge=0.0, le=1.0)
    data_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness of input environmental variables")
    retrieval_relevance: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity / RRF relevance score")
    source_authority: float = Field(..., ge=0.0, le=1.0, description="Credibility weight of sources (FAO/IPCC/UNEP)")
    multi_source_agreement: float = Field(..., ge=0.0, le=1.0, description="Concordance across retrieved literature")
    explanation: str = Field(..., description="Human-readable transparent justification of confidence")


class EcologicalAssessment(BaseModel):
    primary_stressors: List[str] = Field(..., description="Identified environmental bottlenecks")
    compound_risks: List[str] = Field(..., description="Interacting multi-metric risk pathways (>=3 variables)")
    ecological_health_score: float = Field(..., ge=0.0, le=100.0, description="Aggregated ecological health index (0-100)")
    diagnostic_summary: str = Field(..., description="Scientific diagnostic synthesis")


class EnvironmentalAssessmentResponse(BaseModel):
    """Standardized API Response conforming strictly to Requirement #13."""
    assessment: EcologicalAssessment = Field(..., description="Holistic ecological diagnostic")
    recommendations: List[RecommendationItem] = Field(..., description="Evidence-backed action interventions")
    metrics: Dict[str, Any] = Field(..., description="Input, enriched, and projected metric values")
    time_horizon: Dict[str, str] = Field(..., description="Roadmap milestones (short, medium, long term)")
    confidence: ConfidenceBreakdown = Field(..., description="Mathematical confidence breakdown")
    evidence: List[CitationMetadata] = Field(..., description="Consolidated authoritative references cited")
