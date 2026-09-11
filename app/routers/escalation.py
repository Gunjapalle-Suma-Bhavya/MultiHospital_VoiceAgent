"""
Escalation Router (Section 5.39) — Human Escalation REST API.

Endpoints:
  POST /api/v1/escalation/trigger                    — Trigger a new escalation
  GET  /api/v1/escalation/{escalation_id}/context    — Retrieve operator handoff context
  POST /api/v1/escalation/{escalation_id}/resolve    — Mark resolved / transferred back
  GET  /api/v1/escalation/records                    — List escalation records
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.escalation import EscalationEngine, ESCALATION_TRIGGER_REASONS, RESOLUTION_STATUSES

router = APIRouter(tags=["Human Escalation"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class TriggerEscalationRequest(BaseModel):
    session_id: str = Field(..., description="AI conversation session ID")
    trigger_reason: str = Field(..., description="One of the 8 typed trigger reasons")
    hospital_id: Optional[str] = Field(None, description="Hospital scope")
    trace_id: Optional[str] = Field(None, description="Links to OperationTrace")
    failure_count: int = Field(0, description="Number of retries before escalation")
    context_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Patient-facing context for operator handoff. "
            "Keys: patient_intent, conversation_summary, actions_attempted, last_error, patient_info"
        )
    )


class ResolveEscalationRequest(BaseModel):
    resolution_status: str = Field(
        ..., description="RESOLVED or TRANSFERRED_BACK_TO_AI"
    )
    operator_id: Optional[str] = Field(None, description="Human operator identifier")
    operator_notes: Optional[str] = Field(None, description="Free-form resolution notes")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/trigger")
def trigger_escalation(
    req: TriggerEscalationRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger a human escalation.
    Records the escalation with a typed reason, failure count, and authorized context snapshot.
    Returns a ticket ID (ESC-XXXXXXXX) for the operator to reference.
    """
    engine = EscalationEngine(db)
    try:
        result = engine.trigger_escalation(
            session_id=req.session_id,
            trigger_reason=req.trigger_reason,
            hospital_id=req.hospital_id,
            trace_id=req.trace_id,
            failure_count=req.failure_count,
            context_snapshot=req.context_snapshot,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/records")
def list_escalation_records(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital"),
    status: Optional[str] = Query(None, description="Filter by resolution status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db)
):
    """
    List escalation records for the dashboard.
    Filterable by hospital and resolution status.
    """
    engine = EscalationEngine(db)
    records = engine.list_escalation_records(
        hospital_id=hospital_id, status=status, limit=limit
    )
    return {
        "total": len(records),
        "escalation_records": records,
        "trigger_reasons": ESCALATION_TRIGGER_REASONS,
        "resolution_statuses": RESOLUTION_STATUSES,
    }


@router.get("/{escalation_id}/context")
def get_escalation_context(
    escalation_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve the full authorized context package for a human operator.
    Includes patient intent, actions attempted, last error, and operator guidance.
    The patient does not need to repeat their story.
    """
    engine = EscalationEngine(db)
    context = engine.get_escalation_context(escalation_id)
    if context is None:
        raise HTTPException(status_code=404, detail=f"Escalation '{escalation_id}' not found")
    return context


@router.post("/{escalation_id}/resolve")
def resolve_escalation(
    escalation_id: str,
    req: ResolveEscalationRequest,
    db: Session = Depends(get_db)
):
    """
    Mark an escalation as RESOLVED or TRANSFERRED_BACK_TO_AI.
    Records the resolving operator and their notes.
    """
    engine = EscalationEngine(db)
    try:
        result = engine.resolve_escalation(
            escalation_id=escalation_id,
            resolution_status=req.resolution_status,
            operator_id=req.operator_id,
            operator_notes=req.operator_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result is None:
        raise HTTPException(status_code=404, detail=f"Escalation ''{escalation_id}'' not found")
    return result
