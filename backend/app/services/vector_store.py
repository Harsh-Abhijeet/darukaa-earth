"""Vector store and embedding service with pgvector and numpy cosine similarity support."""

import os
import math
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.database import get_engine, get_session_factory
from backend.app.db.models import DocumentChunk, Document, Citation

# Global cache for sentence transformer model
_embedding_model = None

def get_embedding_model():
    """Lazily loads sentence-transformers embedding model unless disabled."""
    global _embedding_model

    # Use lightweight deterministic vectorizer in constrained environments.
    if os.getenv("DISABLE_EMBEDDING_MODEL", "false").lower() == "true":
        logger.info("SentenceTransformer disabled; using deterministic semantic vectorizer.")
        return None

    if _embedding_model is not None:
        return _embedding_model

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer: {settings.EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return _embedding_model
    except Exception as e:
        logger.warning(
            f"SentenceTransformer not available ({e}). Using deterministic agro-ecological semantic vectorizer."
        )
        return None


def generate_embedding(text_content: str, dim: int = 384) -> List[float]:
    """Generates a dense normalized vector for text content."""
    model = get_embedding_model()
    if model is not None:
        try:
            emb = model.encode(text_content, normalize_embeddings=True)
            return emb.tolist()
        except Exception as e:
            logger.warning(f"Embedding model execution failed: {e}. Falling back to semantic hasher.")

    # High-dimensional domain-aware deterministic semantic projection (fallback)
    # Weights ecological keywords to preserve true semantic distance in environmental domain
    vector = np.zeros(dim, dtype=np.float32)
    words = text_content.lower().split()
    
    # Domain keyword amplification
    eco_keywords = {
        "carbon": 10, "soc": 12, "soil": 8, "ph": 10, "moisture": 10,
        "rainfall": 10, "precipitation": 10, "temperature": 8, "drought": 12,
        "biodiversity": 12, "species": 10, "richness": 10, "monoculture": 12,
        "agroforestry": 12, "polyculture": 12, "buffer": 10, "hedgerow": 10,
        "fertilizer": 10, "pesticide": 10, "erosion": 10, "microbial": 12,
        "earthworm": 10, "pollinator": 12, "nitrogen": 8, "fao": 15, "ipcc": 15
    }

    for i, w in enumerate(words):
        h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        weight = eco_keywords.get(w, 1.0)
        vector[idx] += sign * weight

    # Normalize to unit sphere
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two unit-normalized vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
