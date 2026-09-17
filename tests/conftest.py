"""Pytest fixtures and test environment setup."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.db.models import Base
from backend.app.db.database import get_db
from backend.app.main import app
from backend.app.services.rag_service import seed_knowledge_base_from_directory

TEST_DB_FILE = "test_darukaa.db"

@pytest.fixture(scope="session")
def test_engine():
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    engine = create_engine(f"sqlite:///{TEST_DB_FILE}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    # Seed Knowledge Base
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with Session() as db:
        kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))
        seed_knowledge_base_from_directory(db, kb_path)

    yield engine

    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
