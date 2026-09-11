"""
Section 15: Reliability & Failure Handling REST API Router.

Exposes endpoints for:
- Evaluating real-world failures across Voice, Agent, Scheduling, EHR, and Workflows
- Executing controlled retry policies with anti-duplicate guarantees (15.1)
- Demonstrating idempotency across critical operations (15.2)
- Enforcing strict booking verification before confirmation speech (15.3)
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.reliability import (
    FailureDomain,
    FailureResolutionPlan,
)
from app.reliability.failure_handler import ReliabilityAndFailureEngine

router = APIRouter(prefix="/api/v1/reliability", tags=["Section 15: Reliability & Failure Handling"])


class ClassifyFailureRequest(BaseModel):
    domain: FailureDomain
    failure_type: str
    details: Optional[Dict[str, Any]] = None


class ControlledRetryRequest(BaseModel):
    appointment_id: str
    failure_type: str = "API_TIMEOUT"
    max_retries: int = Field(default=3, ge=1, le=5)


class IdempotentOperationRequest(BaseModel):
    idempotency_key: str
    operation_type: str = Field(
        default="APPOINTMENT_CREATION",
        description="One of: APPOINTMENT_CREATION, APPOINTMENT_CANCELLATION, APPOINTMENT_RESCHEDULING, NOTIFICATION_DISPATCH, WORKFLOW_TRIGGER, EHR_INTEGRATION_SYNC"
    )
    payload: Dict[str, Any] = Field(default_factory=dict)


@router.post("/classify-failure", response_model=FailureResolutionPlan)
def classify_failure_and_get_plan(req: ClassifyFailureRequest):
    """
    Classifies a failure across any of the 5 domains (Voice, Agent, Scheduling, EHR, Workflow)
    and returns a deterministic recovery plan with anti-duplicate guarantees.
    """
    return ReliabilityAndFailureEngine.resolve_failure(
        domain=req.domain,
        failure_type=req.failure_type,
        details=req.details
    )


@router.post("/execute-retry")
def execute_controlled_retry(req: ControlledRetryRequest, db: Session = Depends(get_db)):
    """
    Section 15.1: Controlled Retry & Recovery.
    Evaluates retryability, executes verification, avoids duplicates, and reconciles/escalates on retry limit.
    """
    engine = ReliabilityAndFailureEngine(db)
    return engine.execute_controlled_retry(
        appointment_id=req.appointment_id,
        failure_type=req.failure_type,
        max_retries=req.max_retries
    )


@router.post("/idempotent-execute")
def execute_idempotent_operation(req: IdempotentOperationRequest, db: Session = Depends(get_db)):
    """
    Section 15.2: Idempotency Enforcer.
    Guarantees that repeating an operation with the same idempotency key produces identical results
    without duplicate bookings, cancellations, notifications, workflows, or EHR syncs.
    """
    def _sample_action():
        return {
            "processed": True,
            "operation": req.operation_type,
            "received_payload": req.payload,
            "execution_id": f"EXEC-{req.operation_type[:4]}-1001"
        }

    return ReliabilityAndFailureEngine.execute_idempotent_operation(
        idempotency_key=req.idempotency_key,
        operation_type=req.operation_type,
        operation_fn=_sample_action,
        db_session=db
    )


@router.get("/booking-verification/{appointment_id}")
def check_booking_verification_speech(appointment_id: str, db: Session = Depends(get_db)):
    """
    Section 15.3: Booking Verification.
    Strictly evaluates whether the system is authorized to state 'Your appointment is booked'.
    Never communicates booking confirmation until verified with external EHR.
    """
    engine = ReliabilityAndFailureEngine(db)
    return engine.evaluate_booking_confirmation_speech(appointment_id=appointment_id)
