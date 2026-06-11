"""Endpoint for the RAG 'ask the process expert' chat."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.db_models import ChatMessage
from app.models.schemas import ChatRequest, ChatResponse
from app.services import rag

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    answer, sources = rag.answer_question(db, req.process_id, req.question)

    if req.session_id:
        db.add(ChatMessage(session_id=req.session_id, role="agent", content=req.question))
        db.add(ChatMessage(session_id=req.session_id, role="coach", content=answer))
        db.commit()

    return ChatResponse(answer=answer, sources=sources)
