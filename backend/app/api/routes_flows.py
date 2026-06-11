"""Endpoints for listing processes and driving the step-by-step flow guide."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.db_models import CallSession
from app.models.schemas import (
    AdvanceStepRequest,
    AdvanceStepResponse,
    ProcessSummary,
    StartSessionRequest,
    StartSessionResponse,
)
from app.services import flow_engine

router = APIRouter(tags=["flows"])


@router.get("/processes", response_model=list[ProcessSummary])
def list_processes():
    return flow_engine.list_processes()


@router.post("/sessions/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    flow = flow_engine.get_flow(req.process_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Unknown process_id '{req.process_id}'")

    session = CallSession(
        agent_id=req.agent_id,
        process_id=req.process_id,
        current_step_id=flow.start_step_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    current_step = flow_engine.get_step(req.process_id, flow.start_step_id)
    return StartSessionResponse(session_id=session.id, process=flow, current_step=current_step)


@router.post("/sessions/advance", response_model=AdvanceStepResponse)
def advance_step(req: AdvanceStepRequest, db: Session = Depends(get_db)):
    session = db.get(CallSession, req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_step = flow_engine.get_step(session.process_id, session.current_step_id)
    if not current_step:
        raise HTTPException(status_code=400, detail="Current step not found in flow definition")

    if current_step.options:
        if not req.chosen_option_next_step_id:
            raise HTTPException(
                status_code=400,
                detail="This step requires choosing an option (chosen_option_next_step_id).",
            )
        valid_targets = {opt.next_step_id for opt in current_step.options}
        if req.chosen_option_next_step_id not in valid_targets:
            raise HTTPException(status_code=400, detail="Invalid option for current step.")
        next_step_id = req.chosen_option_next_step_id
    else:
        next_step_id = current_step.next_step_id

    if not next_step_id:
        return AdvanceStepResponse(current_step=current_step, finished=True)

    next_step = flow_engine.get_step(session.process_id, next_step_id)
    if not next_step:
        raise HTTPException(status_code=400, detail="Next step not found in flow definition")

    session.current_step_id = next_step.id
    db.commit()

    return AdvanceStepResponse(current_step=next_step, finished=next_step.is_end)
