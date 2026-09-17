"""Scientific Literature Retrieval Tool."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.services.hybrid_search import hybrid_search
from backend.app.core.logging import logger


def retrieve_scientific_literature(
    db: Session,
    query: str,
    top_k: int = 5,
    topic: Optional[str] = None,
    metric: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves authoritative literature chunks with formal citation metadata."""
    logger.info(f"Querying scientific literature: '{query}' (topic={topic}, metric={metric})")
    results = hybrid_search(
        db=db,
        query=query,
        top_k=top_k,
        topic_filter=topic,
        metric_filter=metric
    )
    return results
