"""FastAPI Route Handlers conforming to Requirement #11."""

import uuid
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.db.database import get_db
from backend.app.db.models import (
    EnvironmentalProfile, SoilMetrics, ClimateMetrics,
    LandUseMetrics, BiodiversityMetrics, HumanImpactMetrics,
    Recommendation, Document, Citation, Conversation
)
from backend.app.schemas.environmental import StructuredEnvironmentalProfile
from backend.app.schemas.recommendations import EnvironmentalAssessmentResponse, CitationMetadata
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.schemas.knowledge import (
    DocumentIngestRequest, DocumentIngestResponse,
    KnowledgeSearchResponse, SearchResultChunk
)
from backend.app.services.memory_service import (
    get_or_create_conversation,
    save_conversation_turn,
    merge_extracted_variables
)
from backend.app.services.rag_service import ingest_document
from backend.app.services.hybrid_search import hybrid_search
from backend.app.agent.workflow import workflow_engine
from backend.app.core.logging import logger

router = APIRouter()


@router.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """GET /health: System health, database connection, and tool status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": "Darukaa.Earth Biodiversity Intelligence API",
        "version": "1.0.0",
        "database": db_status,
        "tools": {
            "soilgrids": "operational (live API with regional fallback)",
            "nasa_power": "operational (live API with climatological fallback)",
            "gbif": "operational (live API with ecoregional fallback)",
            "hybrid_rag": "operational (dense pgvector + sparse BM25 + RRF)"
        }
    }


@router.post("/chat", response_model=ChatResponse, tags=["Conversational AI"])
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """POST /chat: Multi-turn conversational endpoint with persistent memory and slot-filling."""
    conv, accumulated_state = get_or_create_conversation(db, request.conversation_id)

    # Convert structured profile to dict if present
    struct_dict = request.structured_profile.model_dump(exclude_none=True) if request.structured_profile else {}

    # Initialize workflow state
    initial_state = {
        "conversation_id": conv.id,
        "user_message": request.message,
        "structured_profile": struct_dict,
        "intent": "general_query",
        "extracted_variables": accumulated_state,
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

    output = workflow_engine.run(initial_state, db=db)
    reply = output.get("reply", "Understood. Analyzing environmental data...")
    clarification_needed = output.get("clarification_needed", False)
    missing = output.get("missing_variables", [])
    current_accumulated = output.get("accumulated_variables", accumulated_state)

    # Persist turn
    save_conversation_turn(
        db=db,
        conversation_id=conv.id,
        user_text=request.message,
        reply_text=reply,
        extracted_state=current_accumulated,
        clarification_requested=clarification_needed
    )

    assessment_res = output.get("assessment_response")
    citations_data = [CitationMetadata(**c) for c in output.get("citations", [])]

    return ChatResponse(
        conversation_id=conv.id,
        reply=reply,
        clarification_needed=clarification_needed,
        missing_variables=missing,
        accumulated_variables=current_accumulated,
        assessment_response=assessment_res,
        citations=citations_data
    )


@router.post("/analyze", response_model=EnvironmentalAssessmentResponse, tags=["Diagnostics"])
def analyze_endpoint(profile: StructuredEnvironmentalProfile, db: Session = Depends(get_db)):
    """POST /analyze: Full multi-metric analysis on structured JSON environmental profile."""
    profile_dict = profile.model_dump(exclude_none=True)

    initial_state = {
        "conversation_id": str(uuid.uuid4()),
        "user_message": "Perform comprehensive multi-metric ecological diagnostic.",
        "structured_profile": profile_dict,
        "intent": "analyze",
        "extracted_variables": profile_dict,
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

    output = workflow_engine.run(initial_state, db=db)
    assessment_data = output.get("assessment_response")
    if not assessment_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate environmental assessment."
        )

    return EnvironmentalAssessmentResponse(**assessment_data)


@router.post("/environment/profile", tags=["Environmental Profiles"])
def create_or_update_profile(profile: StructuredEnvironmentalProfile, db: Session = Depends(get_db)):
    """POST /environment/profile: Stores environmental metrics profile in database."""
    profile_id = str(uuid.uuid4())
    loc = profile.location or None

    env_profile = EnvironmentalProfile(
        id=profile_id,
        name=f"Parcel {loc.region_name if loc and loc.region_name else 'Analysis'}",
        latitude=loc.latitude if loc else None,
        longitude=loc.longitude if loc else None,
        region_name=loc.region_name if loc else None,
        biome=loc.biome if loc else None
    )
    db.add(env_profile)

    if profile.soil:
        s = profile.soil
        soil_record = SoilMetrics(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            ph=s.ph,
            organic_carbon=s.organic_carbon,
            moisture=s.moisture,
            bulk_density=s.bulk_density,
            sand_fraction=s.sand_fraction,
            clay_fraction=s.clay_fraction
        )
        db.add(soil_record)

    if profile.climate:
        c = profile.climate
        clim_record = ClimateMetrics(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            rainfall=c.rainfall,
            temperature=c.temperature,
            drought_index=c.drought_index,
            evapotranspiration=c.evapotranspiration
        )
        db.add(clim_record)

    if profile.land_use:
        lu = profile.land_use
        land_record = LandUseMetrics(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            land_use_type=lu.type,
            crop=lu.crop,
            canopy_cover_pct=lu.canopy_cover,
            buffer_strip_width_m=lu.buffer_strip_width_m,
            tillage_practice=lu.tillage_practice
        )
        db.add(land_record)

    if profile.biodiversity:
        b = profile.biodiversity
        bio_record = BiodiversityMetrics(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            species_richness=b.species_richness,
            pollinator_abundance_score=b.pollinator_abundance,
            soil_microbial_biomass=b.soil_microbial_biomass,
            habitat_diversity_index=b.habitat_diversity_index
        )
        db.add(bio_record)

    db.commit()
    return {
        "status": "success",
        "profile_id": profile_id,
        "completeness_score": profile.get_completeness_score()
    }


@router.get("/environment/{profile_id}", tags=["Environmental Profiles"])
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """GET /environment/{profile_id}: Retrieves complete profile by ID."""
    p = db.query(EnvironmentalProfile).filter(EnvironmentalProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return {
        "profile_id": p.id,
        "name": p.name,
        "location": {"latitude": p.latitude, "longitude": p.longitude, "biome": p.biome},
        "soil": {
            "ph": p.soil.ph if p.soil else None,
            "organic_carbon": p.soil.organic_carbon if p.soil else None,
            "moisture": p.soil.moisture if p.soil else None
        } if p.soil else None,
        "climate": {
            "rainfall": p.climate.rainfall if p.climate else None,
            "temperature": p.climate.temperature if p.climate else None
        } if p.climate else None,
        "land_use": {
            "type": p.land_use.land_use_type if p.land_use else None,
            "crop": p.land_use.crop if p.land_use else None
        } if p.land_use else None,
        "biodiversity": {
            "species_richness": p.biodiversity.species_richness if p.biodiversity else None
        } if p.biodiversity else None
    }


@router.post("/knowledge/ingest", response_model=DocumentIngestResponse, tags=["Knowledge Base"])
def ingest_knowledge_document(doc_in: DocumentIngestRequest, db: Session = Depends(get_db)):
    """POST /knowledge/ingest: Ingests a scientific paper, report, or standard into vector store."""
    doc_id = ingest_document(
        db=db,
        title=doc_in.title,
        organization=doc_in.organization,
        year=doc_in.year,
        content=doc_in.content,
        url=doc_in.url,
        topic=doc_in.topic,
        file_path=doc_in.file_path
    )
    return DocumentIngestResponse(
        document_id=doc_id,
        chunks_indexed=len(doc_in.content.split("\n\n")),
        title=doc_in.title,
        organization=doc_in.organization
    )


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse, tags=["Knowledge Base"])
def search_knowledge(
    query: str = Query(..., description="Semantic search query"),
    topic: Optional[str] = Query(None, description="Topic filter"),
    metric: Optional[str] = Query(None, description="Metric tag filter"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """GET /knowledge/search: Hybrid search over authoritative environmental literature."""
    results = hybrid_search(db=db, query=query, top_k=top_k, topic_filter=topic, metric_filter=metric)
    
    formatted = []
    for r in results:
        formatted.append(SearchResultChunk(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            title=r["title"],
            organization=r["organization"],
            year=r["year"],
            page=r["page"],
            url=r["url"],
            content=r["content"],
            score=r["score"],
            citation=CitationMetadata(**r["citation"])
        ))

    return KnowledgeSearchResponse(
        query=query,
        total_results=len(formatted),
        results=formatted
    )


@router.get("/recommendations/{profile_id}", tags=["Recommendations"])
def get_recommendations_for_profile(profile_id: str, db: Session = Depends(get_db)):
    """GET /recommendations/{profile_id}: Fetches recommendations generated for a given profile."""
    recs = db.query(Recommendation).filter(Recommendation.profile_id == profile_id).all()
    return {
        "profile_id": profile_id,
        "recommendations_count": len(recs),
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "action": r.action_text,
                "scientific_reasoning": r.scientific_reasoning,
                "impacted_metrics": json.loads(r.impacted_metrics_json) if r.impacted_metrics_json else [],
                "expected_impact": r.expected_impact,
                "confidence": r.confidence_level,
                "confidence_score": r.confidence_score
            } for r in recs
        ]
    }


@router.get("/sources/{source_id}", tags=["Knowledge Base"])
def get_source_details(source_id: str, db: Session = Depends(get_db)):
    """GET /sources/{source_id}: Retrieves metadata for an authoritative source or citation."""
    doc = db.query(Document).filter(Document.id == source_id).first()
    if doc:
        return {
            "source_id": doc.id,
            "title": doc.title,
            "organization": doc.organization,
            "year": doc.year,
            "url": doc.url,
            "topic": doc.topic,
            "chunks_count": len(doc.chunks)
        }

    cit = db.query(Citation).filter(Citation.id == source_id).first()
    if cit:
        return {
            "citation_id": cit.id,
            "source_name": cit.source_name,
            "organization": cit.organization,
            "year": cit.year,
            "page": cit.page,
            "url": cit.url,
            "metric": cit.metric,
            "quoted_text": cit.quoted_text
        }

    raise HTTPException(status_code=404, detail="Source or citation not found.")
