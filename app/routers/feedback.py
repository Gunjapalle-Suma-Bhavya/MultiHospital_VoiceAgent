"""
REST API Router for AI Quality Feedback Loop & Continuous Improvement (Section 5.38).
Exposes interaction outcome ingestion, root cause review, improvement application, and re-evaluation verification.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.feedback import AIQualityFeedbackEngine

router = APIRouter(prefix="/api/v1/feedback", tags=["AI Quality Feedback Loop"])


# Pydantic Schemas
class IngestOutcomeRequest(BaseModel):
    interaction_id: str = Field(..., json_schema_extra={"example": "INT-998877"})
    session_id: Optional[str] = Field(None, json_schema_extra={"example": "SESS-DEMO-99"})
    trace_id: Optional[str] = Field(None, json_schema_extra={"example": "TRC-778899"})
    hospital_id: Optional[str] = Field(None, json_schema_extra={"example": "HOSP-101"})
    evaluation_score: float = Field(1.0, json_schema_extra={"example": 0.82})
    is_success: bool = Field(True, json_schema_extra={"example": False})
    is_escalated: bool = Field(False, json_schema_extra={"example": False})
    failure_reason: Optional[str] = Field(None, json_schema_extra={"example": "Doctor availability search timeout"})


class ReviewRootCauseRequest(BaseModel):
    root_cause_category: str = Field(..., json_schema_extra={"example": "PROMPT_AMBIGUITY"})
    review_notes: str = Field(..., json_schema_extra={"example": "Doctor name entity was misrecognized in natural language parser"})


class ApplyImprovementRequest(BaseModel):
    improvement_type: str = Field(..., json_schema_extra={"example": "PROMPT_REFINEMENT"})
    improvement_details: Dict[str, Any] = Field(..., json_schema_extra={"example": {"prompt_template_version": "v2.1", "added_few_shot_examples": 3}})


# Endpoints

@router.post("/ingest", summary="Ingest Interaction Outcome (5.38)")
def ingest_interaction_outcome(req: IngestOutcomeRequest, db: Session = Depends(get_db)):
    """
    Step 1-4: Ingests interaction outcome, classifies success/failure, and creates feedback record.
    """
    record = AIQualityFeedbackEngine.process_interaction_outcome(
        db_session=db,
        interaction_id=req.interaction_id,
        session_id=req.session_id,
        trace_id=req.trace_id,
        hospital_id=req.hospital_id,
        evaluation_score=req.evaluation_score,
        is_success=req.is_success,
        is_escalated=req.is_escalated,
        failure_reason=req.failure_reason
    )
    return {
        "status": "INGESTED",
        "feedback_id": record.id,
        "interaction_id": record.interaction_id,
        "classification": record.classification,
        "evaluation_score": record.evaluation_score,
        "improvement_status": record.improvement_status
    }


@router.post("/{feedback_id}/review", summary="Review & Attribute Root Cause (5.38)")
def review_root_cause(feedback_id: str, req: ReviewRootCauseRequest, db: Session = Depends(get_db)):
    """
    Step 5: Records clinician/admin review notes and assigns root cause category.
    """
    try:
        record = AIQualityFeedbackEngine.review_and_attribute_root_cause(
            db_session=db,
            feedback_id=feedback_id,
            root_cause_category=req.root_cause_category,
            review_notes=req.review_notes
        )
        return {
            "status": "REVIEWED",
            "feedback_id": record.id,
            "root_cause_category": record.root_cause_category,
            "improvement_status": record.improvement_status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{feedback_id}/apply-improvement", summary="Apply System Improvement (5.38)")
def apply_improvement(feedback_id: str, req: ApplyImprovementRequest, db: Session = Depends(get_db)):
    """
    Step 6: Applies prompt, workflow, capability, or EHR integration improvement configuration.
    """
    try:
        record = AIQualityFeedbackEngine.apply_system_improvement(
            db_session=db,
            feedback_id=feedback_id,
            improvement_type=req.improvement_type,
            improvement_details=req.improvement_details
        )
        return {
            "status": "IMPROVEMENT_APPLIED",
            "feedback_id": record.id,
            "improvement_type": record.improvement_type,
            "improvement_status": record.improvement_status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{feedback_id}/re-evaluate", summary="Trigger Re-Evaluation (5.38)")
def trigger_re_evaluation(feedback_id: str, db: Session = Depends(get_db)):
    """
    Step 7: Triggers re-evaluation benchmark suite and verifies improvement score.
    """
    try:
        return AIQualityFeedbackEngine.trigger_re_evaluation(db, feedback_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/records", summary="Get Feedback Lifecycle History (5.38)")
def get_feedback_records(hospital_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Returns complete engineering lifecycle feedback history across all 7 steps.
    """
    return AIQualityFeedbackEngine.get_feedback_lifecycle_history(db, hospital_id=hospital_id)
