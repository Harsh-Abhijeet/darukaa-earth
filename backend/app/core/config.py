"""Application Configuration and Environmental Settings for Darukaa.Earth.

Provides type-safe configuration via pydantic-settings, supporting
PostgreSQL with pgvector for production and automatic fallback to
local SQLite + cosine vector search for offline/testing scenarios.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Darukaa.Earth Biodiversity Intelligence"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Database Configuration (PostgreSQL with pgvector)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://darukaa:darukaa_earth_secret@localhost:5432/darukaa_earth",
        description="Async PostgreSQL connection URI. If unreachable, system auto-falls back to SQLite."
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg2://darukaa:darukaa_earth_secret@localhost:5432/darukaa_earth",
        description="Sync PostgreSQL URI for migrations and vector initialization."
    )
    ENABLE_SQLITE_FALLBACK: bool = True
    SQLITE_PATH: str = "darukaa_local.db"

    # Vector / Embedding Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 6

    # LLM API Keys (Optional - System operates deterministically with domain reasoning rules if keys absent)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1

    # External Environmental API Endpoints
    SOILGRIDS_API_URL: str = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    NASA_POWER_API_URL: str = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    GBIF_API_URL: str = "https://api.gbif.org/v1/occurrence/search"
    EXTERNAL_API_TIMEOUT_SECONDS: int = 5

    # CORS & Security
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60


settings = Settings()
