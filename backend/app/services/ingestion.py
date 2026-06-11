"""Ingestion pipeline: read process knowledge docs, chunk, embed, and store in pgvector.

Knowledge docs live under data/knowledge/<process_id>/*.md (or .txt).
Run with:  python -m app.services.ingestion
"""
import os
import re

import voyageai
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal, engine, Base
from app.models.db_models import KnowledgeChunk

settings = get_settings()

CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 150


def _knowledge_dir() -> str:
    here = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
    return os.path.normpath(os.path.join(here, settings.knowledge_dir))


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Naive paragraph-aware chunking with overlap."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        # try to break on a paragraph/sentence boundary
        boundary = text.rfind("\n\n", start, end)
        if boundary == -1:
            boundary = text.rfind(". ", start, end)
        if boundary == -1 or boundary <= start:
            boundary = end
        chunks.append(text[start:boundary].strip())
        start = max(boundary - overlap, start + 1)
    return [c for c in chunks if c]


def _embed(texts: list[str]) -> list[list[float]]:
    if not settings.voyage_api_key:
        raise RuntimeError("VOYAGE_API_KEY is not set in .env")
    client = voyageai.Client(api_key=settings.voyage_api_key)
    result = client.embed(texts, model=settings.embedding_model, input_type="document")
    return result.embeddings


def ingest_all(db: Session | None = None) -> int:
    """Walk data/knowledge/<process_id>/*.md, chunk + embed + upsert into the DB.

    Returns the number of chunks ingested.
    """
    Base.metadata.create_all(bind=engine)
    own_session = db is None
    db = db or SessionLocal()
    total = 0
    try:
        knowledge_dir = _knowledge_dir()
        if not os.path.isdir(knowledge_dir):
            print(f"No knowledge dir found at {knowledge_dir}")
            return 0

        for process_id in os.listdir(knowledge_dir):
            process_path = os.path.join(knowledge_dir, process_id)
            if not os.path.isdir(process_path):
                continue

            # Clear existing chunks for this process before re-ingesting.
            db.query(KnowledgeChunk).filter(KnowledgeChunk.process_id == process_id).delete()

            for filename in os.listdir(process_path):
                if not filename.lower().endswith((".md", ".txt")):
                    continue
                filepath = os.path.join(process_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()

                chunks = _chunk_text(text)
                if not chunks:
                    continue

                embeddings = _embed(chunks)
                for chunk_text, embedding in zip(chunks, embeddings):
                    db.add(
                        KnowledgeChunk(
                            process_id=process_id,
                            source=filename,
                            content=chunk_text,
                            embedding=embedding,
                        )
                    )
                    total += 1

        db.commit()
        return total
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    n = ingest_all()
    print(f"Ingested {n} chunks.")
