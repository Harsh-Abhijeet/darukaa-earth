"""Database engine connection management with transparent fallback."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models import Base

# Engine configuration
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    db_url = settings.DATABASE_SYNC_URL
    try:
        # Test if PostgreSQL is available
        logger.info(f"Attempting connection to primary database: {db_url.split('@')[-1]}")
        test_engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Attempt to register pgvector extension if available
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector extension verified on PostgreSQL.")
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension: {e}")
        _engine = test_engine
        logger.info("Connected successfully to PostgreSQL + pgvector.")
    except Exception as e:
        if settings.ENABLE_SQLITE_FALLBACK:
            sqlite_file = os.path.abspath(settings.SQLITE_PATH)
            logger.warning(
                f"PostgreSQL unreachable ({e}). Gracefully falling back to local SQLite: {sqlite_file}"
            )
            _engine = create_engine(
                f"sqlite:///{sqlite_file}",
                connect_args={"check_same_thread": False}
            )
        else:
            raise e

    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db():
    """Dependency for FastAPI route handlers."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
