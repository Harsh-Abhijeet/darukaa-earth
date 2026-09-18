"""SQLAlchemy ORM Models for Darukaa.Earth Biodiversity Intelligence Platform.

Conforms to Requirement #14:
- users
- conversations
- messages
- environmental_profiles
- soil_metrics
- climate_metrics
- land_use_metrics
- biodiversity_metrics
- human_impact_metrics
- documents
- document_chunks (with vector embeddings)
- citations
- recommendations
- recommendation_evidence
"""

import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Float, Integer, ForeignKey, Text,
    DateTime, Boolean, TypeDecorator
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class AdaptiveVector(TypeDecorator):
    """Adaptive Vector type: uses pgvector's Vector in PostgreSQL, JSON in SQLite."""
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 384, **kwargs):
        super().__init__(**kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (list, tuple)):
            return json.dumps(list(value))
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    role = Column(String(64), default="environmental_analyst")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    profiles = relationship("EnvironmentalProfile", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    title = Column(String(255), default="Environmental Consultation")
    active_profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    recommendations = relationship("Recommendation", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id"), nullable=False, index=True)
    sender = Column(String(32), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    extracted_state_json = Column(Text, nullable=True)  # JSON snapshot of extracted variables
    clarification_requested = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class EnvironmentalProfile(Base):
    __tablename__ = "environmental_profiles"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    name = Column(String(255), default="Farm / Land Parcel Profile")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    region_name = Column(String(128), nullable=True)
    biome = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="profiles")
    soil = relationship("SoilMetrics", uselist=False, back_populates="profile", cascade="all, delete-orphan")
    climate = relationship("ClimateMetrics", uselist=False, back_populates="profile", cascade="all, delete-orphan")
    land_use = relationship("LandUseMetrics", uselist=False, back_populates="profile", cascade="all, delete-orphan")
    biodiversity = relationship("BiodiversityMetrics", uselist=False, back_populates="profile", cascade="all, delete-orphan")
    human_impact = relationship("HumanImpactMetrics", uselist=False, back_populates="profile", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="profile", cascade="all, delete-orphan")


class SoilMetrics(Base):
    __tablename__ = "soil_metrics"

    id = Column(String(64), primary_key=True, index=True)
    profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), unique=True, nullable=False)
    ph = Column(Float, nullable=True)
    organic_carbon = Column(Float, nullable=True)  # wt %
    moisture = Column(Float, nullable=True)        # %
    bulk_density = Column(Float, nullable=True)    # g/cm3
    sand_fraction = Column(Float, nullable=True)   # %
    clay_fraction = Column(Float, nullable=True)   # %
    source = Column(String(64), default="user_input")  # user_input, isric_soilgrids, regional_baseline

    profile = relationship("EnvironmentalProfile", back_populates="soil")


class ClimateMetrics(Base):
    __tablename__ = "climate_metrics"

    id = Column(String(64), primary_key=True, index=True)
    profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), unique=True, nullable=False)
    rainfall = Column(Float, nullable=True)        # mm/yr
    temperature = Column(Float, nullable=True)     # deg C mean
    drought_index = Column(Float, nullable=True)
    evapotranspiration = Column(Float, nullable=True)
    source = Column(String(64), default="user_input")  # user_input, nasa_power, regional_baseline

    profile = relationship("EnvironmentalProfile", back_populates="climate")


class LandUseMetrics(Base):
    __tablename__ = "land_use_metrics"

    id = Column(String(64), primary_key=True, index=True)
    profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), unique=True, nullable=False)
    land_use_type = Column(String(128), nullable=True)  # monoculture, polyculture, agroforestry, fallow
    crop = Column(String(128), nullable=True)
    canopy_cover_pct = Column(Float, nullable=True)
    buffer_strip_width_m = Column(Float, nullable=True)
    tillage_practice = Column(String(64), nullable=True)

    profile = relationship("EnvironmentalProfile", back_populates="land_use")


class BiodiversityMetrics(Base):
    __tablename__ = "biodiversity_metrics"

    id = Column(String(64), primary_key=True, index=True)
    profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), unique=True, nullable=False)
    species_richness = Column(Integer, nullable=True)
    pollinator_abundance_score = Column(Float, nullable=True)
    soil_microbial_biomass = Column(Float, nullable=True)
    habitat_diversity_index = Column(Float, nullable=True)
    source = Column(String(64), default="user_input")

    profile = relationship("EnvironmentalProfile", back_populates="biodiversity")


class HumanImpactMetrics(Base):
    __tablename__ = "human_impact_metrics"

    id = Column(String(64), primary_key=True, index=True)
    profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), unique=True, nullable=False)
    chemical_fertilizer_kg_ha = Column(Float, nullable=True)
    pesticide_applications_per_year = Column(Integer, nullable=True)
    deforestation_proximity_km = Column(Float, nullable=True)
    erosion_risk_score = Column(Float, nullable=True)

    profile = relationship("EnvironmentalProfile", back_populates="human_impact")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    organization = Column(String(128), nullable=False)
    year = Column(Integer, nullable=False)
    url = Column(String(512), nullable=True)
    topic = Column(String(128), nullable=True)
    file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    section_title = Column(String(255), nullable=True)
    page_number = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    metric_tags = Column(String(255), nullable=True)
    embedding = Column(AdaptiveVector(dim=384), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(64), primary_key=True, index=True)
    chunk_id = Column(String(64), ForeignKey("document_chunks.id"), nullable=True)
    source_name = Column(String(255), nullable=False)
    organization = Column(String(128), nullable=False)
    year = Column(Integer, nullable=False)
    page = Column(String(64), nullable=True)
    url = Column(String(512), nullable=True)
    topic = Column(String(128), nullable=True)
    metric = Column(String(128), nullable=True)
    quoted_text = Column(Text, nullable=True)

    chunk = relationship("DocumentChunk", back_populates="citations")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True, index=True)
    profile_id = Column(String(64), ForeignKey("environmental_profiles.id"), nullable=True, index=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    action_text = Column(Text, nullable=False)
    scientific_reasoning = Column(Text, nullable=False)
    impacted_metrics_json = Column(Text, nullable=False)
    expected_impact = Column(Text, nullable=False)
    time_horizon = Column(String(32), nullable=False)
    confidence_level = Column(String(16), nullable=False)  # High, Medium, Low
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("EnvironmentalProfile", back_populates="recommendations")
    conversation = relationship("Conversation", back_populates="recommendations")
    evidence = relationship("RecommendationEvidence", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationEvidence(Base):
    __tablename__ = "recommendation_evidence"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), ForeignKey("recommendations.id"), nullable=False, index=True)
    chunk_id = Column(String(64), ForeignKey("document_chunks.id"), nullable=True)
    citation_text = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.85)

    recommendation = relationship("Recommendation", back_populates="evidence")
