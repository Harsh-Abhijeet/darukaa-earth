"""Pydantic schemas for knowledge ingestion, search, and citation retrieval."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.recommendations import CitationMetadata


class DocumentIngestRequest(BaseModel):
    title: str = Field(..., description="Title of the scientific paper, report, or standard")
    organization: str = Field(..., description="Issuing organization (e.g. FAO, IPCC, UNEP, ISRIC, GBIF)")
    year: int = Field(..., description="Publication year")
    url: Optional[str] = Field(None, description="Direct URL or DOI")
    topic: Optional[str] = Field(None, description="Domain topic")
    content: str = Field(..., description="Raw text or markdown content to chunk and index")
    file_path: Optional[str] = Field(None)


class DocumentIngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int
    title: str
    organization: str
    status: str = "success"


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    topic_filter: Optional[str] = Field(None, description="Optional topic filter")
    metric_filter: Optional[str] = Field(None, description="Optional metric tag filter")
    top_k: int = Field(5, ge=1, le=20)


class SearchResultChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    organization: str
    year: int
    page: Optional[str]
    url: Optional[str]
    content: str
    score: float
    citation: CitationMetadata


class KnowledgeSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultChunk]
