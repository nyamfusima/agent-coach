"""Ingestion pipeline: read process knowledge docs, chunk, embed, and store in pgvector.

Knowledge docs live under data/knowledge/<process_id>/*.{md,txt,pdf}.

Run with:
    python -m app.services.ingestion                 # (re)ingest every process
    python -m app.services.ingestion --process billing   # only one process
"""
import argparse
import os
import re
import time

import voyageai
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal, engine, Base
from app.models.db_models import KnowledgeChunk

settings = get_settings()

CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 150
SUPPORTED_EXTS = (".md", ".txt", ".pdf")
# Embed in batches and pause between them so we stay within Voyage's free-tier
# limits (3 requests/min, 10K tokens/min) when no payment method is on file.
# This whole knowledge base is only ~4K tokens, so a large batch sends it in a
# single request — minimising rate-limit exposure. Lower this only if a much
# bigger knowledge base pushes one request over the 10K-tokens/min cap.
EMBED_BATCH = 256
EMBED_PAUSE_SECONDS = 21


def _knowledge_dir() -> str:
    here = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
    return os.path.normpath(os.path.join(here, settings.knowledge_dir))


def _read_file(path: str) -> str:
    """Read a knowledge doc to plain text. PDFs are extracted page by page."""
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Sliding-window chunking with overlap, preferring paragraph/sentence cuts.

    The window always advances by at least ``size//2 - overlap`` characters, so
    text with long runs of single-newline lines (e.g. step lists) can't make it
    degenerate into hundreds of tiny overlapping chunks.
    """
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        # Try to end the chunk on a paragraph/sentence boundary, but only if it
        # falls in the back half of the window — never reset the cursor backwards.
        if end < len(text):
            boundary = text.rfind("\n\n", start, end)
            if boundary == -1:
                boundary = text.rfind(". ", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def _embed(texts: list[str], *, max_retries: int = 5) -> list[list[float]]:
    if not settings.voyage_api_key:
        raise RuntimeError("VOYAGE_API_KEY is not set in .env")
    client = voyageai.Client(api_key=settings.voyage_api_key)
    delay = 20
    for attempt in range(max_retries):
        try:
            result = client.embed(
                texts, model=settings.embedding_model, input_type="document"
            )
            return result.embeddings
        except voyageai.error.RateLimitError:
            if attempt == max_retries - 1:
                raise
            print(f"  rate limited by Voyage; waiting {delay}s then retrying...")
            time.sleep(delay)
            delay = min(delay * 2, 90)


def ingest_all(db: Session | None = None, process_filter: str | None = None) -> int:
    """Chunk + embed + store knowledge docs into pgvector.

    Walks data/knowledge/<process_id>/*.{md,txt,pdf}. If ``process_filter`` is
    given, only that process is re-ingested; all other processes are left
    untouched. Returns the number of chunks ingested.
    """
    Base.metadata.create_all(bind=engine)
    own_session = db is None
    db = db or SessionLocal()
    try:
        knowledge_dir = _knowledge_dir()
        if not os.path.isdir(knowledge_dir):
            print(f"No knowledge dir found at {knowledge_dir}")
            return 0

        process_ids = sorted(
            p for p in os.listdir(knowledge_dir)
            if os.path.isdir(os.path.join(knowledge_dir, p))
        )
        if process_filter:
            if process_filter not in process_ids:
                print(f"No knowledge folder for process '{process_filter}' in {knowledge_dir}")
                return 0
            process_ids = [process_filter]

        # First pass: clear existing chunks for the processes being (re)ingested
        # and collect every (process, source, text) chunk. We embed them together
        # in batched requests rather than one request per file (which trips the
        # free-tier rate limit).
        records: list[tuple[str, str, str]] = []
        for process_id in process_ids:
            process_path = os.path.join(knowledge_dir, process_id)
            db.query(KnowledgeChunk).filter(KnowledgeChunk.process_id == process_id).delete()

            for filename in sorted(os.listdir(process_path)):
                if not filename.lower().endswith(SUPPORTED_EXTS):
                    continue
                text = _read_file(os.path.join(process_path, filename))
                chunks = _chunk_text(text)
                print(f"  {process_id}/{filename}: {len(chunks)} chunk(s)")
                for chunk in chunks:
                    records.append((process_id, filename, chunk))

        if not records:
            db.commit()
            return 0

        # Second pass: embed in batches, pausing between them for the rate limit.
        total = 0
        for start in range(0, len(records), EMBED_BATCH):
            batch = records[start : start + EMBED_BATCH]
            embeddings = _embed([r[2] for r in batch])
            for (process_id, filename, chunk), embedding in zip(batch, embeddings):
                db.add(
                    KnowledgeChunk(
                        process_id=process_id,
                        source=filename,
                        content=chunk,
                        embedding=embedding,
                    )
                )
                total += 1
            print(f"  embedded {total}/{len(records)} chunks")
            if start + EMBED_BATCH < len(records):
                time.sleep(EMBED_PAUSE_SECONDS)

        db.commit()
        return total
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest knowledge docs into pgvector.")
    parser.add_argument(
        "--process",
        help="Only (re)ingest this process_id; other processes are left untouched.",
    )
    args = parser.parse_args()

    if not settings.voyage_api_key.strip():
        raise SystemExit(
            "ERROR: VOYAGE_API_KEY is not configured in backend/.env, so embedding "
            "cannot run. Contact your admin."
        )

    scope = f"process '{args.process}'" if args.process else "all processes"
    print(f"Ingesting {scope}...")
    n = ingest_all(process_filter=args.process)
    print(f"Done. Ingested {n} chunks for {scope}.")
