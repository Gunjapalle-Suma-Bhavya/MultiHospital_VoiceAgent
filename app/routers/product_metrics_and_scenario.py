"""
REST API Router for Section 23 Product Metrics and Section 24 Example End-to-End Scenario.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.analytics import ProductMetricsService
from app.workflows import EndToEndScenarioService

router = APIRouter(prefix="/api/v1", tags=["Product Metrics & End-to-End Scenario"])


class ExecuteScenarioRequest(BaseModel):
    patient_name: str = Field("Patient A", json_schema_extra={"example": "Patient A"})
    patient_phone: str = Field("+1-555-SHOULDER", json_schema_extra={"example": "+1-555-SHOULDER"})
    run_questionnaire: bool = Field(True, json_schema_extra={"example": True})


# =============================================================================
# Section 23: Product Metrics
# =============================================================================

@router.get("/metrics/product", summary="Get Platform Product Metrics (Section 23)")
def get_product_metrics(
    hospital_id: Optional[str] = Query(None, description="Optional hospital filter"),
    db: Session = Depends(get_db)
):
    """
    Returns platform-wide product metrics measuring business outcomes and system reliability:
    1. Patient Experience (completion, booking time, abandonment, clarification, satisfaction)
    2. Scheduling (success, double-booking prevention, cancellation, rescheduling, slot utilization)
    3. AI (latency, capability success, escalation, task completion, context resolution, safety)
    4. EHR / Integration (success, error, recovery, duration, verification, sync, reconciliation, duplicate prevention)
    5. Workflow (success, failure, retry, duration, escalation, duplicate execution)
    6. Notifications (delivery, failure, latency)
    7. Hospital (active doctors, volume, utilization, questionnaire completion, AI-assisted booking)
    """
    return ProductMetricsService.get_all_product_metrics(db=db, hospital_id=hospital_id)


# =============================================================================
# Section 24: Example End-to-End Scenario
# =============================================================================

@router.post("/scenario/end-to-end/execute", summary="Execute Canonical Example End-to-End Scenario (Section 24)")
def execute_end_to_end_scenario(
    req: ExecuteScenarioRequest,
    db: Session = Depends(get_db)
):
    """
    Executes the canonical Section 24 healthcare intake scenario:
    - Patient utterance: 'shoulder pain for the last week'
    - AI searches Hospitals, Doctors, Calendars, Slots
    - Presents options (Dr. Sharma at City Hospital 4 PM, Dr. Rao at Care Hospital 5:30 PM)
    - Patient selects Dr. Sharma at 4 PM
    - Booking Capability validates Patient, Doctor, Slot, creates booking
    - EHR Integration maps Patient/Provider/Facility, creates external EHR-88421, verifies record, syncs internal APT-1024 (Confirmed)
    - Triggers Reminder, Questionnaire, Notifications, Analytics, Audit
    - Collects Pre-Visit Questionnaire (Shoulder pain: Yes, Duration: 1 week, Previous treatment: No)
    - Generates multi-role perspectives for Doctor, Hospital Admin, and Platform Admin.
    """
    return EndToEndScenarioService.execute_scenario(
        db=db,
        patient_name=req.patient_name,
        patient_phone=req.patient_phone,
        run_questionnaire=req.run_questionnaire
    )


@router.get("/scenario/end-to-end/status", summary="Get Latest Scenario Multi-Role Status (Section 24)")
def get_scenario_status(db: Session = Depends(get_db)):
    """
    Returns the latest executed scenario state and multi-role views.
    """
    return EndToEndScenarioService.execute_scenario(db=db)
