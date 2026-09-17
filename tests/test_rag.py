"""Tests for Knowledge Ingestion, Hybrid Search, and Citation Tracking."""

import pytest
from backend.app.services.rag_service import chunk_text
from backend.app.services.vector_store import generate_embedding, cosine_similarity
from backend.app.services.hybrid_search import hybrid_search, bm25_score_tokens


def test_chunking():
    text = (
        "# Section 1\nSoil carbon is critical.\n" * 10 +
        "\n# Section 2\nRainfall patterns dictate planting windows.\n" * 10
    )
    chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 2
    assert any("Soil carbon" in c["content"] for c in chunks)


def test_embedding_normalization():
    emb = generate_embedding("Soil organic carbon in semi-arid wheat monoculture")
    assert len(emb) == 384
    sim = cosine_similarity(emb, emb)
    assert pytest.approx(sim, 0.001) == 1.0


def test_bm25_relevance():
    query_tokens = ["carbon", "soil"]
    doc1 = ["soil", "organic", "carbon", "levels", "are", "depleted"]
    doc2 = ["rainfall", "and", "temperature", "extremes"]
    score1 = bm25_score_tokens(query_tokens, doc1)
    score2 = bm25_score_tokens(query_tokens, doc2)
    assert score1 > score2


def test_hybrid_search_with_citations(db_session):
    results = hybrid_search(db_session, query="soil organic carbon microbial biomass", top_k=3)
    assert len(results) > 0
    first = results[0]
    assert "citation" in first
    assert "source_name" in first["citation"]
    assert "organization" in first["citation"]
    assert "year" in first["citation"]
