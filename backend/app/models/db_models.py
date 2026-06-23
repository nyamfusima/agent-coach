"""SQLAlchemy ORM models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector

from app.core.db import Base
from app.core.config import get_settings

settings = get_settings()


class KnowledgeChunk(Base):
    """A chunk of process/knowledge documentation, embedded for RAG retrieval."""

    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(String, index=True, nullable=False)  # e.g. "billing_query"
    source = Column(String, nullable=False)  # filename / doc title
    content = Column(Text, nullable=False)
    embedding = Column(Vector(settings.embedding_dimensions))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CallSession(Base):
    """A live call session for one agent, tracking flow progress and chat history."""

    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, index=True, nullable=False)
    agent_name = Column(String, nullable=True)
    team_name = Column(String, nullable=True)
    process_id = Column(String, nullable=False)
    current_step_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    """A single message in the agent <-> coach chat for a session (for logging/analytics)."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True, nullable=False)
    role = Column(String, nullable=False)  # "agent" | "coach"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FlaggedAnswer(Base):
    """A coach answer an agent marked as unhelpful (thumbs down), for supervisor review."""

    __tablename__ = "flagged_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True, nullable=True)
    process_id = Column(String, index=True, nullable=True)
    agent_id = Column(String, nullable=True)
    agent_name = Column(String, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
