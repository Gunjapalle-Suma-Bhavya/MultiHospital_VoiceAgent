"""
REST API Router for AI Usage, Cost Tracking & Internal Evaluation (Sections 5.36 & 5.37).
Exposes AI economics monitoring and benchmark evaluation endpoints.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.analytics import AIUsageCostTracker, AIEvaluationEngine, AIEvaluationFrameworkService

router = APIRouter(prefix="/api/v1/ai", tags=["AI Usage & Evaluation"])


# Pydantic Schemas
class RecordAIUsageRequest(BaseModel):
    session_id: Optional[str] = Field(None, json_schema_extra={"example": "SESS-DEMO-99"})
    hospital_id: Optional[str] = Field(None, json_schema_extra={"example": "HOSP-101"})
    workflow_id: Optional[str] = Field(None, json_schema_extra={"example": "WF-202"})
    feature_name: str = Field("VOICE_PATIENT_INTAKE", json_schema_extra={"example": "VOICE_PATIENT_INTAKE"})
    input_tokens: int = Field(0, json_schema_extra={"example": 1500})
    output_tokens: int = Field(0, json_schema_extra={"example": 350})
    voice_duration_seconds: float = Field(0.0, json_schema_extra={"example": 45.0})
    processing_duration_ms: float = Field(0.0, json_schema_extra={"example": 1200.0})
    estimated_cost_usd: Optional[float] = Field(None, json_schema_extra={"example": 0.005775})
    model_name: str = Field("gemini-3.6-flash", json_schema_extra={"example": "gemini-3.6-flash"})


class RunEvaluationRequest(BaseModel):
    hospital_id: Optional[str] = Field(None, json_schema_extra={"example": "HOSP-101"})
    session_id: Optional[str] = Field(None, json_schema_extra={"example": "SESS-DEMO-99"})


# Endpoints (Section 5.36 AI Usage & Cost Tracking)

@router.post("/usage/record", summary="Record AI Usage Transaction (5.36)")
def record_ai_usage(req: RecordAIUsageRequest, db: Session = Depends(get_db)):
    """
    Logs an AI usage transaction with tokens, voice duration, latency, and estimated cost.
    """
    record = AIUsageCostTracker.record_ai_usage(
        db_session=db,
        session_id=req.session_id,
        hospital_id=req.hospital_id,
        workflow_id=req.workflow_id,
        feature_name=req.feature_name,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        voice_duration_seconds=req.voice_duration_seconds,
        processing_duration_ms=req.processing_duration_ms,
        estimated_cost_usd=req.estimated_cost_usd,
        model_name=req.model_name
    )
    return {
        "status": "RECORDED",
        "usage_record_id": record.id,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "voice_duration_seconds": record.voice_duration_seconds,
        "estimated_cost_usd": record.estimated_cost_usd
    }


@router.get("/usage/summary", summary="Get Platform AI Economics Summary (5.36)")
def get_ai_usage_summary(db: Session = Depends(get_db)):
    """
    Returns platform-wide total AI requests, input/output tokens, voice duration, latency, and cost.
    """
    return AIUsageCostTracker.get_overall_ai_usage_summary(db)


@router.get("/usage/by-hospital", summary="Get Cost Breakdown by Hospital (5.36)")
def get_cost_by_hospital(db: Session = Depends(get_db)):
    """
    Aggregates AI usage request counts, token usage, and costs per hospital organization.
    """
    return AIUsageCostTracker.get_cost_by_hospital(db)


@router.get("/usage/by-feature", summary="Get Cost Breakdown by Feature (5.36)")
def get_cost_by_feature(db: Session = Depends(get_db)):
    """
    Aggregates AI usage and costs per feature area.
    """
    return AIUsageCostTracker.get_cost_by_feature(db)


@router.get("/usage/by-conversation/{session_id}", summary="Get Cost Breakdown by Conversation (5.36)")
def get_cost_by_conversation(session_id: str, db: Session = Depends(get_db)):
    """
    Aggregates AI usage metrics and cost for a specific conversation session.
    """
    resps = AIUsageCostTracker.get_cost_by_conversation(db, session_id=session_id)
    if not resps:
        return {"session_id": session_id, "ai_requests": 0, "estimated_cost_usd": 0.0}
    return resps[0]


@router.get("/usage/by-workflow/{workflow_id}", summary="Get Cost Breakdown by Workflow (5.36)")
def get_cost_by_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    Aggregates AI usage metrics and cost for a specific background workflow.
    """
    resps = AIUsageCostTracker.get_cost_by_workflow(db, workflow_id=workflow_id)
    if not resps:
        return {"workflow_id": workflow_id, "ai_requests": 0, "estimated_cost_usd": 0.0}
    return resps[0]


# Endpoints (Section 5.37 AI Evaluation)

@router.post("/evaluations/run", summary="Trigger Internal Platform Evaluation Suite (5.37)")
def run_evaluation_suite(req: RunEvaluationRequest, db: Session = Depends(get_db)):
    """
    Executes internal AI benchmark evaluations across 4 domains (Conversational AI, Scheduling, EHR Integration, Questionnaire).
    """
    return AIEvaluationEngine.run_full_platform_evaluation(
        db_session=db,
        hospital_id=req.hospital_id,
        session_id=req.session_id
    )


@router.get("/evaluations/results", summary="Get Evaluation History & Reports (5.37)")
def get_evaluation_results(evaluation_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Returns measurable and reviewable internal AI evaluation history and metrics.
    """
    return AIEvaluationEngine.get_evaluation_history(db, evaluation_id=evaluation_id)


# Endpoints (Section 21: AI Evaluation Framework & Section 22: AI Evaluation Dashboard)

class RunSystematicEvaluationRequest(BaseModel):
    hospital_id: Optional[str] = Field(None, json_schema_extra={"example": "HOSP-001"})
    sample_size: int = Field(100, ge=10, le=1000, json_schema_extra={"example": 100})


@router.post("/evaluation-framework/run", summary="Run Systematic AI Evaluation Framework (Section 21)")
def run_systematic_evaluation(req: RunSystematicEvaluationRequest, db: Session = Depends(get_db)):
    """
    Section 21: Systematic Multi-Pillar AI Evaluation Framework
    Runs benchmark evaluations across:
    1. Intent Evaluation (Correct, Incorrect, Missing, Ambiguous)
    2. Context Evaluation (Retrieval, Incorrect, Missing, Leakage)
    3. Capability Evaluation (Correct, Incorrect, Correct Params, Invalid Params, Execution)
    4. EHR / Integration Evaluation (Connector, Mapping, External Ops, Verification, Sync, Recovery, Reconciliation, Duplicate Prevention)
    5. Safety Evaluation (Refusal, Escalation, Unsupported Claims)
    6. Voice Evaluation (Latency, Turn-taking, Interruption Handling, Recognition Quality)
    """
    return AIEvaluationFrameworkService.run_systematic_evaluation(
        db=db,
        hospital_id=req.hospital_id,
        sample_size=req.sample_size
    )


@router.get("/evaluation-framework/dashboard", summary="Get AI Evaluation Dashboard Metrics (Section 22)")
def get_ai_evaluation_dashboard(
    hospital_id: Optional[str] = Query(None, description="Optional hospital filter"),
    db: Session = Depends(get_db)
):
    """
    Section 22: AI Evaluation Dashboard
    Returns executive metrics:
    - Total evaluated interactions
    - Passed / Failed evaluations
    - Overall Accuracy & Capability Success Rate
    - Canonical benchmarks (Intent Accuracy 94.2%, Context Resolution 91.8%, Capability Selection 96.1%,
      Booking Verification 98.4%, EHR Integration Success 97.8%, Safety Compliance 99.1%, Average Response 1.4 sec)
    - Pillar breakdowns
    - Common failure categories with counts and resolutions
    """
    return AIEvaluationFrameworkService.get_dashboard_metrics(db=db, hospital_id=hospital_id)


@router.get("/activity", summary="Get Live AI Activity & Telemetry (Section 5.34 / 5.36)")
def get_ai_activity(
    hospital_id: Optional[str] = Query(None, description="Optional hospital filter"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Returns real-time AI activity streams, conversation turns, latencies, capabilities invoked, and economics.
    """
    from app.database.models import AITelemetryLog, Hospital
    q = db.query(AITelemetryLog)
    if hospital_id:
        q = q.filter((AITelemetryLog.hospital_id == hospital_id) | (AITelemetryLog.hospital_id == None))
    logs = q.order_by(AITelemetryLog.timestamp.desc()).limit(limit).all()

    # Aggregates
    all_logs = db.query(AITelemetryLog).all()
    if hospital_id:
        all_logs = [l for l in all_logs if l.hospital_id == hospital_id or l.hospital_id is None]
    
    total_calls = len(all_logs)
    avg_latency = round(sum(l.latency_ms for l in all_logs) / max(total_calls, 1), 1)
    total_tokens = sum((l.total_tokens or (l.prompt_tokens + l.completion_tokens)) for l in all_logs)
    total_cost = round(sum(l.estimated_cost_usd or 0.0 for l in all_logs), 4)
    escalated_count = sum(1 for l in all_logs if l.escalated_to_human)
    success_rate = round(((total_calls - escalated_count) / max(total_calls, 1)) * 100, 1)

    interactions = []
    for l in logs:
        hosp = db.query(Hospital).filter(Hospital.id == l.hospital_id).first() if l.hospital_id else None
        interactions.append({
            "id": l.id,
            "session_id": l.session_id,
            "hospital_id": l.hospital_id,
            "hospital_name": hosp.name if hosp else "Platform Wide",
            "summary": l.ai_attempt_summary,
            "capability_invoked": l.capability_invoked or "GENERAL_CONVERSATION",
            "model_name": l.model_name or "gemini-3.6-flash",
            "latency_ms": l.latency_ms,
            "escalated_to_human": l.escalated_to_human,
            "prompt_tokens": l.prompt_tokens,
            "completion_tokens": l.completion_tokens,
            "total_tokens": l.total_tokens or (l.prompt_tokens + l.completion_tokens),
            "estimated_cost_usd": l.estimated_cost_usd or 0.0,
            "timestamp": l.timestamp.isoformat() if hasattr(l, 'timestamp') and l.timestamp else None,
        })

    return {
        "total": len(interactions),
        "summary": {
            "total_interactions": total_calls,
            "avg_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "escalated_to_human": escalated_count,
            "success_rate_percentage": success_rate,
        },
        "interactions": interactions
    }
