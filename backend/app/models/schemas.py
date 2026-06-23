"""Pydantic request/response schemas for the API."""
from typing import Optional
from pydantic import BaseModel


# --- Flows ---

class FlowOption(BaseModel):
    label: str
    next_step_id: str


class FlowStep(BaseModel):
    id: str
    title: str
    instructions: str
    # If empty -> single "Next" button moves to `next_step_id`.
    options: list[FlowOption] = []
    next_step_id: Optional[str] = None
    is_end: bool = False


class FlowDefinition(BaseModel):
    process_id: str
    name: str
    description: str = ""
    start_step_id: str
    steps: list[FlowStep]


class ProcessSummary(BaseModel):
    process_id: str
    name: str
    description: str = ""


# --- Sessions / Flow progress ---

class StartSessionRequest(BaseModel):
    agent_id: str
    process_id: str
    agent_name: Optional[str] = None
    team_name: Optional[str] = None


class StartSessionResponse(BaseModel):
    session_id: int
    process: FlowDefinition
    current_step: FlowStep


class AdvanceStepRequest(BaseModel):
    session_id: int
    chosen_option_next_step_id: Optional[str] = None  # required if current step has options


class AdvanceStepResponse(BaseModel):
    current_step: FlowStep
    finished: bool = False


# --- Chat / RAG ---

class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    process_id: str
    question: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    confidence: float = 1.0          # 0..1, from retrieval similarity
    low_confidence: bool = False     # true when retrieval was weak / no knowledge


# --- Feedback ---

class FlagAnswerRequest(BaseModel):
    session_id: Optional[int] = None
    process_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    question: str
    answer: str


# --- Admin / supervisor ---

class AdminSession(BaseModel):
    session_id: int
    agent_id: str
    agent_name: Optional[str] = None
    team_name: Optional[str] = None
    process_id: str
    process_name: str
    created_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    message_count: int = 0


class AdminQuestion(BaseModel):
    process_id: str
    process_name: str
    question: str
    count: int


class AdminFlaggedAnswer(BaseModel):
    id: int
    process_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    question: str
    answer: str
    created_at: Optional[str] = None
