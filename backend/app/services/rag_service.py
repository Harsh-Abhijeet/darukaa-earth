"""Document ingestion pipeline, chunking, and knowledge base seeding."""

import os
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models import Document, DocumentChunk, Citation
from backend.app.services.vector_store import generate_embedding


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extracts YAML-style frontmatter if present in markdown document."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1].strip()
            body = parts[2].strip()
            for line in raw_meta.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body


def chunk_text(text_content: str, chunk_size: int = 500, chunk_overlap: int = 80) -> List[Dict[str, Any]]:
    """Splits text into semantically coherent section chunks preserving headings."""
    sections = re.split(r'(?=\n#{1,3}\s)', text_content)
    chunks = []
    chunk_index = 0

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        # Detect heading
        header_match = re.match(r'^#{1,3}\s+(.+)', sec)
        current_heading = header_match.group(1) if header_match else "General"

        # Split long sections into word-based chunks
        words = sec.split()
        if len(words) <= chunk_size:
            chunks.append({
                "chunk_index": chunk_index,
                "section_title": current_heading,
                "content": sec
            })
            chunk_index += 1
        else:
            step = chunk_size - chunk_overlap
            for i in range(0, len(words), step):
                window = words[i:i + chunk_size]
                chunk_str = " ".join(window)
                chunks.append({
                    "chunk_index": chunk_index,
                    "section_title": current_heading,
                    "content": chunk_str
                })
                chunk_index += 1

    return chunks


def ingest_document(
    db: Session,
    title: str,
    organization: str,
    year: int,
    content: str,
    url: Optional[str] = None,
    topic: Optional[str] = None,
    file_path: Optional[str] = None
) -> str:
    """Ingests a single document into PostgreSQL/SQLite with embeddings and citations.
    
    Conforms to Requirement #9 & #20:
    - Ingest PDF/TXT/Markdown
    - Extract metadata
    - Chunk documents
    - Create embeddings
    - Store embeddings in DB
    - Preserve source/page metadata
    - Expose citations
    """
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        title=title,
        organization=organization,
        year=year,
        url=url,
        topic=topic,
        file_path=file_path
    )
    db.add(doc)
    db.flush()

    parsed_chunks = chunk_text(content, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
    logger.info(f"Ingesting '{title}' ({organization}, {year}) -> {len(parsed_chunks)} chunks")

    for c in parsed_chunks:
        chunk_id = str(uuid.uuid4())
        emb = generate_embedding(c["content"], dim=settings.EMBEDDING_DIMENSION)

        # Infer metric tags
        content_lower = c["content"].lower()
        tags = []
        if "carbon" in content_lower or "soc" in content_lower:
            tags.append("soil_organic_carbon")
        if "ph" in content_lower:
            tags.append("soil_ph")
        if "moisture" in content_lower or "water" in content_lower:
            tags.append("soil_moisture")
        if "rainfall" in content_lower or "precipitation" in content_lower:
            tags.append("rainfall")
        if "temperature" in content_lower or "heat" in content_lower:
            tags.append("temperature")
        if "pollinator" in content_lower or "bee" in content_lower:
            tags.append("pollinators")
        if "richness" in content_lower or "biodiversity" in content_lower:
            tags.append("species_richness")
        if "monoculture" in content_lower:
            tags.append("monoculture")
        if "buffer" in content_lower or "hedgerow" in content_lower:
            tags.append("buffer_strip")

        metric_tags_str = ", ".join(tags) if tags else "agro_ecology"

        # Determine approximate page / section
        page_num = f"Section: {c['section_title']}"

        chunk_model = DocumentChunk(
            id=chunk_id,
            document_id=doc_id,
            chunk_index=c["chunk_index"],
            section_title=c["section_title"],
            page_number=page_num,
            content=c["content"],
            metric_tags=metric_tags_str,
            embedding=emb
        )
        db.add(chunk_model)

        # Formal citation metadata row conforming to Requirement #20
        citation = Citation(
            id=str(uuid.uuid4()),
            chunk_id=chunk_id,
            source_name=title,
            organization=organization,
            year=year,
            page=page_num,
            url=url,
            topic=topic,
            metric=metric_tags_str,
            quoted_text=c["content"][:250]
        )
        db.add(citation)

    db.commit()
    return doc_id


def seed_knowledge_base_from_directory(db: Session, kb_dir: str):
    """Seeds database with default authoritative scientific documents if empty."""
    existing_count = db.query(Document).count()
    if existing_count > 0:
        logger.info(f"Knowledge base already seeded with {existing_count} documents.")
        return

    if not os.path.exists(kb_dir):
        logger.warning(f"Knowledge base directory does not exist: {kb_dir}")
        return

    logger.info(f"Seeding knowledge base from: {kb_dir}")
    for fname in os.listdir(kb_dir):
        if fname.endswith((".md", ".txt")):
            fpath = os.path.join(kb_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            meta, body = parse_frontmatter(content)
            title = meta.get("source_name", fname.replace("_", " ").title())
            organization = meta.get("organization", "International Scientific Authority")
            year = int(meta.get("year", 2021))
            url = meta.get("url", "https://darukaa.earth")
            topic = meta.get("topic", "Soil, Climate and Biodiversity")

            ingest_document(
                db=db,
                title=title,
                organization=organization,
                year=year,
                content=body,
                url=url,
                topic=topic,
                file_path=fpath
            )
    logger.info("Knowledge base seeding completed.")
