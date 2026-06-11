"""RAG service: retrieve relevant process-knowledge chunks and ask Claude
to answer the agent's question conversationally, grounded in that context.
"""
import anthropic
import voyageai
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db_models import KnowledgeChunk

settings = get_settings()

TOP_K = 5

SYSTEM_PROMPT = """You are an internal assistant helping a customer service agent \
DURING a live call. The agent will ask you questions about policy, process, or what \
to say to the customer.

Rules:
- Answer ONLY using the provided context. If the context doesn't cover it, say so \
plainly and suggest the agent escalate or check with a supervisor — do NOT guess \
or make up policy.
- Be concise and conversational, like a helpful, knowledgeable colleague — not a \
formal document. The agent is mid-call and needs a quick, usable answer.
- If relevant, suggest exact wording the agent could say to the customer.
- Do not pad your answer with caveats, generic disclaimers, or "as an AI" language.
"""


def _embed_query(text: str) -> list[float]:
    if not settings.voyage_api_key:
        raise RuntimeError("VOYAGE_API_KEY is not set in .env")
    client = voyageai.Client(api_key=settings.voyage_api_key)
    result = client.embed([text], model=settings.embedding_model, input_type="query")
    return result.embeddings[0]


def retrieve(db: Session, process_id: str, question: str, top_k: int = TOP_K) -> list[KnowledgeChunk]:
    query_embedding = _embed_query(question)
    stmt = (
        select(KnowledgeChunk)
        .where(KnowledgeChunk.process_id == process_id)
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return list(db.scalars(stmt))


def answer_question(db: Session, process_id: str, question: str) -> tuple[str, list[str]]:
    chunks = retrieve(db, process_id, question)

    if not chunks:
        return (
            "I don't have any process knowledge loaded for this yet, so I can't "
            "give you a grounded answer. Check with a supervisor for now.",
            [],
        )

    context = "\n\n---\n\n".join(f"[Source: {c.source}]\n{c.content}" for c in chunks)
    sources = sorted({c.source for c in chunks})

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Process knowledge context:\n\n{context}\n\n"
                    f"---\n\nAgent's question: {question}"
                ),
            }
        ],
    )
    answer = "".join(block.text for block in response.content if block.type == "text")
    return answer, sources
