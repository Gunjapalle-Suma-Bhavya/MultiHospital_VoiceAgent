"""
REST API Router for Operational Observability & Correlation Traceability (Sections 5.34 & 5.35).
Exposes operation trace management, 16-step lifecycle profiling, cross-component correlation aggregation,
and operational analytics.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.observability import TraceManager, ObservabilityService

router = APIRouter(prefix="/api/v1/observability", tags=["Operational Observability"])


# Pydantic Schemas
class StartTraceRequest(BaseModel):
    session_id: str = Field(..., json_schema_extra={"example": "SESS-DEMO-99"})
    hospital_id: Optional[str] = Field(None, json_schema_extra={"example": "HOSP-UUID-101"})
    patient_id: Optional[str] = Field(None, json_schema_extra={"example": "PAT-UUID-202"})
    appointment_id: Optional[str] = Field(None, json_schema_extra={"example": "APPT-UUID-303"})
    operation_name: str = Field("PATIENT_ACCESS_BOOKING_LIFECYCLE", json_schema_extra={"example": "PATIENT_ACCESS_BOOKING_LIFECYCLE"})
    correlation_id: Optional[str] = Field(None, json_schema_extra={"example": "CORR-778899"})
    metadata: Optional[Dict[str, Any]] = None


class RecordStepRequest(BaseModel):
    step_name: str = Field(..., json_schema_extra={"example": "CHECK_AVAILABILITY"})
    component_type: str = Field(..., json_schema_extra={"example": "CAPABILITY_CALL"})
    latency_ms: float = Field(0.0, json_schema_extra={"example": 45.2})
    status: str = Field("SUCCESS", json_schema_extra={"example": "SUCCESS"})
    error_message: Optional[str] = Field(None, json_schema_extra={"example": "API timeout on Epic FHIR adapter"})
    external_system_name: Optional[str] = Field(None, json_schema_extra={"example": "EPIC_MYCHART"})
    retry_count: int = Field(0, json_schema_extra={"example": 1})
    details: Optional[Dict[str, Any]] = None


class FinalizeTraceRequest(BaseModel):
    status: str = Field("COMPLETED", json_schema_extra={"example": "COMPLETED"})
    recovery_succeeded: bool = Field(False, json_schema_extra={"example": True})
    reconciliation_occurred: bool = Field(False, json_schema_extra={"example": False})
    escalated_to_human: bool = Field(False, json_schema_extra={"example": False})
    metadata: Optional[Dict[str, Any]] = None


# Endpoints

@router.post("/traces/start", summary="Start Operation Trace (5.34)")
def start_trace(req: StartTraceRequest, db: Session = Depends(get_db)):
    """
    Starts an end-to-end operation trace and issues/associates a unified correlation_id.
    Auto-records Step #1: CALL_STARTED.
    """
    trace = TraceManager.start_trace(
        db_session=db,
        session_id=req.session_id,
        hospital_id=req.hospital_id,
        patient_id=req.patient_id,
        appointment_id=req.appointment_id,
        operation_name=req.operation_name,
        correlation_id=req.correlation_id,
        metadata=req.metadata
    )
    return {
        "status": "STARTED",
        "trace_id": trace.trace_id,
        "correlation_id": trace.correlation_id,
        "session_id": trace.session_id,
        "started_at": trace.started_at.isoformat() if trace.started_at else None
    }


@router.post("/traces/{trace_id}/step", summary="Record Lifecycle Step (5.34)")
def record_step(trace_id: str, req: RecordStepRequest, db: Session = Depends(get_db)):
    """
    Appends a granular step to an active operation trace.
    Tracks latency, error diagnostics, external system failures, and retry counts.
    """
    try:
        step = TraceManager.record_step(
            db_session=db,
            trace_id=trace_id,
            step_name=req.step_name,
            component_type=req.component_type,
            latency_ms=req.latency_ms,
            status=req.status,
            error_message=req.error_message,
            external_system_name=req.external_system_name,
            retry_count=req.retry_count,
            details=req.details
        )
        return {
            "status": "RECORDED",
            "trace_id": trace_id,
            "step_number": step.step_number,
            "step_name": step.step_name,
            "latency_ms": step.latency_ms
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/traces/{trace_id}/finalize", summary="Finalize Operation Trace (5.34)")
def finalize_trace(trace_id: str, req: FinalizeTraceRequest, db: Session = Depends(get_db)):
    """
    Finalizes an operation trace, calculates total latency, appends CALL_COMPLETED,
    and records recovery/reconciliation/escalation outcomes.
    """
    try:
        trace = TraceManager.finalize_trace(
            db_session=db,
            trace_id=trace_id,
            status=req.status,
            recovery_succeeded=req.recovery_succeeded,
            reconciliation_occurred=req.reconciliation_occurred,
            escalated_to_human=req.escalated_to_human,
            metadata=req.metadata
        )
        return {
            "status": "FINALIZED",
            "trace_id": trace.trace_id,
            "final_status": trace.status,
            "total_latency_ms": trace.total_latency_ms,
            "recovery_succeeded": trace.recovery_succeeded,
            "reconciliation_occurred": trace.reconciliation_occurred,
            "escalated_to_human": trace.escalated_to_human
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/traces/{trace_id}", summary="Get End-to-End Operation Trace Details (5.34)")
def get_trace_details(trace_id: str, db: Session = Depends(get_db)):
    """
    Returns complete operation trace summary, step latency breakdown, and diagnostics.
    """
    res = ObservabilityService.get_trace_details(db, trace_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/correlation/{correlation_id}", summary="Get Unified Cross-Component Correlation Timeline (5.35)")
def get_correlation_timeline(correlation_id: str, db: Session = Depends(get_db)):
    """
    Aggregates connected events across all 10 platform component layers sharing a common correlation ID.
    """
    return ObservabilityService.get_correlation_timeline(db, correlation_id)


@router.get("/analytics", summary="Get Operational Analytics & Latency Breakdown (5.34)")
def get_observability_analytics(db: Session = Depends(get_db)):
    """
    Returns platform-wide operational observability metrics, step latency profiling, and failure distributions.
    """
    return ObservabilityService.get_observability_analytics(db)
