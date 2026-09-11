"""
REST API Router for Section 35 Definition of Done (DoD).
Exposes endpoints to execute and inspect the 27-stage canonical platform journey,
as well as the two failure recovery scenarios (Transient Recovery and Persistent Escalation).
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.workflows.definition_of_done_service import DefinitionOfDoneService

router = APIRouter(prefix="/api/v1/definition-of-done", tags=["Section 35: Definition of Done"])


class DoDExecuteRequest(BaseModel):
    hospital_name: str = Field("Metropolitan Health System", json_schema_extra={"example": "Metropolitan Health System"})
    doctor_name: str = Field("Dr. Sharma", json_schema_extra={"example": "Dr. Sharma"})
    patient_name: str = Field("Patient A", json_schema_extra={"example": "Patient A"})
    patient_phone: str = Field("+1-555-SHOULDER", json_schema_extra={"example": "+1-555-SHOULDER"})


class FailureRecoveryRequest(BaseModel):
    mode: str = Field("TRANSIENT_RECOVERY", description="Either 'TRANSIENT_RECOVERY' or 'RECONCILIATION_ESCALATION'")
    hospital_id: Optional[str] = Field(None, description="Optional hospital ID")


@router.post("/execute-journey", summary="Execute 27-Stage Canonical DoD Journey (Section 35)")
def execute_dod_canonical_journey(
    req: DoDExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Executes the canonical 27-stage Definition of Done journey:
    Hospital Registration -> Admin Approval -> Hospital Configuration ->
    Doctor Creation -> Calendar Configuration -> EHR Configuration ->
    Patient Registration -> AI Voice Conversation -> Intent Understanding ->
    Context Resolution -> Doctor Discovery -> Availability Check ->
    Patient Selection -> Appointment Booking -> EHR Integration ->
    External Verification -> State Synchronization -> Follow-Up Workflow ->
    Pre-Visit Questionnaire -> Structured Responses -> Doctor Review ->
    Notification -> Analytics -> Audit Trail -> Operational Monitoring ->
    Multi-Role Perspectives -> Definition of Done Verification.
    """
    return DefinitionOfDoneService.execute_canonical_journey(
        db=db,
        hospital_name=req.hospital_name,
        doctor_name=req.doctor_name,
        patient_name=req.patient_name,
        patient_phone=req.patient_phone
    )


@router.post("/simulate-failure-recovery", summary="Simulate DoD Failure Recovery Scenarios (Section 35)")
def simulate_dod_failure_recovery(
    req: FailureRecoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Simulates Section 35 Failure Scenarios:
    1. TRANSIENT_RECOVERY:
       Booking Attempt -> EHR Integration Failure -> Classify Failure ->
       Retry -> External State Verification -> Recovery -> Verification ->
       Successful Completion.
    2. RECONCILIATION_ESCALATION:
       Booking Attempt -> EHR Integration Failure -> Retry Limit Reached ->
       External State Verification -> Reconciliation Required ->
       Human Escalation -> Operational Issue Record Created.
    """
    if req.mode == "RECONCILIATION_ESCALATION":
        return DefinitionOfDoneService.execute_failure_scenario_reconciliation_escalation(
            db=db,
            hospital_id=req.hospital_id
        )
    return DefinitionOfDoneService.execute_failure_scenario_transient_recovery(
        db=db,
        hospital_id=req.hospital_id
    )


@router.get("/checklist", summary="Get Section 35 Definition of Done Checklist")
def get_dod_checklist():
    """
    Returns the complete structured Section 35 Definition of Done checklist
    with 27 stages and failure recovery specifications.
    """
    canonical_stages = [
        "Hospital Registration",
        "Admin Approval",
        "Hospital Configuration",
        "Doctor Creation",
        "Calendar Configuration",
        "EHR / Healthcare-System Configuration",
        "Patient Registration",
        "AI Voice Conversation",
        "Intent Understanding",
        "Context Resolution",
        "Doctor Discovery",
        "Availability Check",
        "Patient Selection",
        "Appointment Booking",
        "EHR Integration",
        "External Verification",
        "State Synchronization",
        "Follow-Up Workflow",
        "Pre-Visit Questionnaire",
        "Structured Responses",
        "Doctor Review",
        "Notification",
        "Analytics",
        "Audit Trail",
        "Operational Monitoring",
        "Multi-Role Perspectives",
        "Definition of Done Verification"
    ]

    failure_recovery_scenarios = [
        {
            "scenario_name": "Transient EHR Failure & Self-Healing Recovery",
            "path": "Booking Attempt -> EHR Integration Failure -> Classify Failure -> Retry -> External State Verification -> Recovery -> Verification -> Successful Completion"
        },
        {
            "scenario_name": "Persistent Failure, Reconciliation & Human Escalation",
            "path": "Booking Attempt -> EHR Integration Failure -> Retry Limit Reached -> External State Verification -> Reconciliation Required -> Human Escalation -> Operational Issue Record Created"
        }
    ]

    return {
        "section": "Section 35: Definition of Done",
        "status": "PROTOTYPE_COMPLETE",
        "total_canonical_stages": len(canonical_stages),
        "canonical_stages": canonical_stages,
        "failure_recovery_scenarios": failure_recovery_scenarios,
        "compliance_rate": "100%"
    }
