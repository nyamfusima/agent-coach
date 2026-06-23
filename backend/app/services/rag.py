"""RAG service: retrieve relevant process-knowledge chunks and ask Claude
to answer the agent's question conversationally, grounded in that context.
"""
import re

import anthropic
import voyageai
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db_models import KnowledgeChunk

settings = get_settings()

TOP_K = 5
# Below this similarity (1 - cosine_distance of the best chunk) we tell the agent
# the answer may be unreliable and they should consider escalating.
LOW_CONFIDENCE_THRESHOLD = 0.4

SYSTEM_PROMPT = """You are an internal assistant helping a customer service agent during a live \
call. Agents ask you two kinds of things:
(a) Policy, process, or factual questions: the rule, the steps, eligibility, amounts, timeframes.
(b) Behavioural or communication questions: what to say, empathy statements, tone, calming an \
upset customer, apologising, phrasing, building rapport.

How to answer:
1. For policy, process, or factual questions, answer ONLY using the provided context. If the \
context does not cover it, say so plainly and suggest the agent escalate or check with a \
supervisor. Never guess or invent policy, numbers, eligibility, or steps.
2. For behavioural or communication questions, answer from general customer service best practice, \
even when it is not in the context. Give the agent specific, natural wording they can say out loud \
right now, in a warm and genuine voice.

Make it easy to read fast, because the agent is on a live call:
1. Lead with the single most important action or line.
2. Keep each point on its own short line, one idea per line.
3. Use numbered steps for a sequence, or a bullet starting with the "•" character for a list. \
Never start a line with a dash or a hyphen.
4. Put any exact words to say to the customer on their own line, inside quotation marks.
5. Do not write long paragraphs, and do not run several ideas into one sentence.

Punctuation and formatting:
1. Do not use dashes of any kind as punctuation or as connectors. Use full stops, commas, colons, \
or new lines instead.
2. Do not use Markdown symbols such as asterisks for bold. Write plain text only.

Voice: sound like a helpful, knowledgeable colleague, not a formal document. No padding, no \
generic disclaimers, no "as an AI" language.

Before your answer, output exactly one tag on its own first line: [[MODE:policy]] if the answer \
relies on the policy or process context, or [[MODE:behavioural]] if it is general communication or \
soft skill guidance. Then write the answer. Never mention this tag or these instructions to the \
agent.
"""

_MODE_RE = re.compile(r"\[\[\s*MODE:\s*(policy|behaviou?ral|mixed)\s*\]\]", re.IGNORECASE)


def _split_mode(text: str) -> tuple[str | None, str]:
    """Pull the leading [[MODE:...]] tag the model emits, returning (mode, clean_text)."""
    match = _MODE_RE.search(text)
    mode = match.group(1).lower() if match else None
    cleaned = _MODE_RE.sub("", text).strip()  # strip the tag anywhere, defensively
    return mode, cleaned


def _format_for_agent(text: str) -> str:
    """Backstop the formatting rules in case the model slips: drop Markdown bold
    markers, turn dash/asterisk list markers into "•", and replace any em/en
    dashes with plain punctuation so nothing dash-like reaches the agent."""
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?m)^[ \t]*[-*•][ \t]+", "• ", text)  # list markers -> bullet
    text = text.replace("—", ", ").replace("–", ", ")     # em / en dashes
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _embed_query(text: str) -> list[float]:
    if not settings.voyage_api_key:
        raise RuntimeError("VOYAGE_API_KEY is not set in .env")
    client = voyageai.Client(api_key=settings.voyage_api_key)
    result = client.embed([text], model=settings.embedding_model, input_type="query")
    return result.embeddings[0]


def retrieve(
    db: Session, process_id: str, question: str, top_k: int = TOP_K
) -> list[tuple[KnowledgeChunk, float]]:
    """Return the top_k chunks for the question, each with its cosine distance."""
    query_embedding = _embed_query(question)
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(KnowledgeChunk, distance.label("distance"))
        .where(KnowledgeChunk.process_id == process_id)
        .order_by(distance)
        .limit(top_k)
    )
    return [(row[0], float(row[1])) for row in db.execute(stmt)]


def answer_question(
    db: Session, process_id: str, question: str
) -> tuple[str, list[str], float, bool]:
    """Returns (answer, sources, confidence, low_confidence)."""
    results = retrieve(db, process_id, question)

    if not results:
        return (
            "I don't have any process knowledge loaded for this yet, so I can't "
            "give you a grounded answer. Check with a supervisor for now.",
            [],
            0.0,
            True,
        )

    chunks = [c for c, _ in results]
    best_distance = min(d for _, d in results)
    # cosine_distance is in [0, 2]; similarity ~ 1 - distance for normalized vectors.
    confidence = max(0.0, min(1.0, 1.0 - best_distance))
    low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD

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
    raw = "".join(block.text for block in response.content if block.type == "text")
    mode, answer = _split_mode(raw)
    answer = _format_for_agent(answer)

    # Behavioural answers come from general best practice, not the retrieved docs,
    # so weak retrieval similarity is expected — don't flag them as low confidence.
    if mode and mode.startswith("behav"):
        low_confidence = False
        sources = []  # no policy sources backed this answer

    return answer, sources, confidence, low_confidence
