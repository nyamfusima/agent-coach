"""Endpoint for the RAG 'ask the process expert' chat."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models.db_models import ChatMessage, FlaggedAnswer
from app.models.schemas import ChatRequest, ChatResponse, FlagAnswerRequest
from app.services import rag

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

UNAVAILABLE_MSG = (
    "⚠️ The process assistant hit a temporary problem reaching its AI services. "
    "You can keep using the call steps; for policy questions, check with a "
    "supervisor for now."
)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    missing = get_settings().missing_ai_keys()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"API key not configured ({', '.join(missing)}). Contact your admin.",
        )

    try:
        answer, sources, confidence, low_confidence = rag.answer_question(
            db, req.process_id, req.question
        )
    except Exception:
        # Transient external failures (rate limits, timeouts) — degrade gracefully
        # so the agent isn't blocked mid-call; full traceback is logged server-side.
        logger.exception("chat failed for process_id=%s", req.process_id)
        return ChatResponse(
            answer=UNAVAILABLE_MSG, sources=[], confidence=0.0, low_confidence=True
        )

    if req.session_id:
        db.add(ChatMessage(session_id=req.session_id, role="agent", content=req.question))
        db.add(ChatMessage(session_id=req.session_id, role="coach", content=answer))
        db.commit()

    return ChatResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        low_confidence=low_confidence,
    )


@router.post("/feedback/flag", status_code=201)
def flag_answer(req: FlagAnswerRequest, db: Session = Depends(get_db)):
    """Record an unhelpful (thumbs-down) coach answer for supervisor review."""
    flagged = FlaggedAnswer(
        session_id=req.session_id,
        process_id=req.process_id,
        agent_id=req.agent_id,
        agent_name=req.agent_name,
        question=req.question,
        answer=req.answer,
    )
    db.add(flagged)
    db.commit()
    db.refresh(flagged)
    return {"id": flagged.id, "status": "flagged"}
