"""Read-only supervisor endpoints (no auth for V1).

Powers the /admin page: recent call sessions, most-asked questions per process,
and flagged (thumbs-down) answers for improving the knowledge base.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.db_models import CallSession, ChatMessage, FlaggedAnswer
from app.models.schemas import AdminFlaggedAnswer, AdminQuestion, AdminSession
from app.services import flow_engine

router = APIRouter(prefix="/admin", tags=["admin"])


def _process_names() -> dict[str, str]:
    return {p.process_id: p.name for p in flow_engine.list_processes()}


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


@router.get("/sessions", response_model=list[AdminSession])
def recent_sessions(limit: int = 50, db: Session = Depends(get_db)):
    names = _process_names()
    msg_counts = dict(
        db.execute(
            select(ChatMessage.session_id, func.count())
            .where(ChatMessage.role == "agent")
            .group_by(ChatMessage.session_id)
        ).all()
    )

    sessions = (
        db.execute(select(CallSession).order_by(desc(CallSession.created_at)).limit(limit))
        .scalars()
        .all()
    )

    out = []
    for s in sessions:
        end = s.ended_at or s.updated_at
        duration = int((end - s.created_at).total_seconds()) if (end and s.created_at) else None
        out.append(
            AdminSession(
                session_id=s.id,
                agent_id=s.agent_id,
                agent_name=s.agent_name,
                team_name=s.team_name,
                process_id=s.process_id,
                process_name=names.get(s.process_id, s.process_id),
                created_at=_iso(s.created_at),
                duration_seconds=duration if duration and duration >= 0 else None,
                message_count=msg_counts.get(s.id, 0),
            )
        )
    return out


@router.get("/questions", response_model=list[AdminQuestion])
def common_questions(limit: int = 50, db: Session = Depends(get_db)):
    names = _process_names()
    rows = db.execute(
        select(
            CallSession.process_id,
            ChatMessage.content,
            func.count().label("cnt"),
        )
        .join(CallSession, CallSession.id == ChatMessage.session_id)
        .where(ChatMessage.role == "agent")
        .group_by(CallSession.process_id, ChatMessage.content)
        .order_by(desc("cnt"))
        .limit(limit)
    ).all()

    return [
        AdminQuestion(
            process_id=pid,
            process_name=names.get(pid, pid),
            question=content,
            count=cnt,
        )
        for pid, content, cnt in rows
    ]


@router.get("/flagged", response_model=list[AdminFlaggedAnswer])
def flagged_answers(limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.execute(select(FlaggedAnswer).order_by(desc(FlaggedAnswer.created_at)).limit(limit))
        .scalars()
        .all()
    )
    return [
        AdminFlaggedAnswer(
            id=f.id,
            process_id=f.process_id,
            agent_id=f.agent_id,
            agent_name=f.agent_name,
            question=f.question,
            answer=f.answer,
            created_at=_iso(f.created_at),
        )
        for f in rows
    ]
