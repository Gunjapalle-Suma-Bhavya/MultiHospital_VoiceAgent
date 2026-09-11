"""
REST API Router for AI Usage, Cost Tracking & Internal Evaluation (Sections 5.36 & 5.37).
Exposes AI economics monitoring and benchmark evaluation endpoints.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.analytics import AIUsageCostTracker, AIEvaluationEngine

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
