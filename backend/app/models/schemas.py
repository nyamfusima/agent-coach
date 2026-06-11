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


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
