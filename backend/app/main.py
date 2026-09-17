"""FastAPI Application Entrypoint for Darukaa.Earth Biodiversity Intelligence Platform."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.database import get_engine, get_session_factory
from backend.app.db.models import Base
from backend.app.services.rag_service import seed_knowledge_base_from_directory
from backend.app.api.endpoints import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event: initializes database tables and seeds scientific knowledge base."""
    logger.info("Starting Darukaa.Earth Biodiversity Intelligence Platform...")
    engine = get_engine()
    
    # Initialize all database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")

    # Seed authoritative scientific documents
    session_factory = get_session_factory()
    with session_factory() as db:
        # Look for knowledge base directory in project root or relative
        kb_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
        )
        seed_knowledge_base_from_directory(db, kb_path)

    yield
    logger.info("Shutting down Darukaa.Earth API.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production prototype AI Environmental Scientist for the Darukaa.Earth Hackathon. "
        "Integrates SoilGrids, NASA POWER, GBIF, Hybrid pgvector RAG, and multi-metric reasoning across >= 3 variables."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount endpoints at root and under /api/v1
app.include_router(api_router, prefix="")
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
