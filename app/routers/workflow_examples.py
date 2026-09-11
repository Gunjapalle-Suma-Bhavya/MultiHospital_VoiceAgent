"""
REST API Router for Section 20 Workflow Examples.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.workflows.canonical_examples import CanonicalWorkflowExamplesService

router = APIRouter(prefix="/api/v1/workflow-examples", tags=["Workflow Examples (Section 20)"])


class WorkflowTriggerRequest(BaseModel):
    workflow_code: str  # '20.1', '20.2', '20.3', '20.4', '20.5', '20.6'
    appointment_id: Optional[str] = None
    questionnaire_id: Optional[str] = "Q-CLINICAL-INTAKE-01"
    session_id: Optional[str] = None
    reason: Optional[str] = "PATIENT_EXPLICIT_REQUEST_HUMAN"
    simulated_retry_success: Optional[bool] = True
    new_start_datetime: Optional[datetime] = None


@router.post("/execute")
def execute_workflow_example(req: WorkflowTriggerRequest, db: Session = Depends(get_db)):
    """
    Executes any of the 6 Section 20 canonical workflows:
    - 20.1: Appointment Reminder
    - 20.2: Questionnaire Reminder
    - 20.3: Failed Booking Recovery
    - 20.4: Human Escalation
    - 20.5: Appointment Cancellation
    - 20.6: Appointment Rescheduling
    """
    svc = CanonicalWorkflowExamplesService(db)

    # Resolve an existing appointment or create mock for demonstration
    appt_id = req.appointment_id
    from app.database.models import Appointment, Hospital, Doctor, AppointmentStatus
    appt = None
    if appt_id:
        appt = db.query(Appointment).filter(Appointment.id == appt_id).first()

    if not appt and req.workflow_code in ["20.1", "20.2", "20.3", "20.5", "20.6"]:
        appt = db.query(Appointment).first()
        if not appt:
            # Create a demonstration appointment
            hosp = db.query(Hospital).first()
            if not hosp:
                hosp = Hospital(name="Demo Hospital", code="DEMO_HOSP")
                db.add(hosp)
                db.commit()
            doc = db.query(Doctor).first()
            if not doc:
                doc = Doctor(hospital_id=hosp.id, name="Dr. Demo", specialty="General")
                db.add(doc)
                db.commit()
            appt = Appointment(
                id=appt_id or "DEMO-APPT-SEC20",
                hospital_id=hosp.id,
                doctor_id=doc.id,
                patient_name="Demo Patient",
                patient_phone="+15550001122",
                start_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2),
                end_datetime=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, minutes=30),
                status=AppointmentStatus.CONFIRMED,
                is_ehr_verified=True
            )
            db.add(appt)
            db.commit()
            db.refresh(appt)

        appt_id = appt.id

    if req.workflow_code == "20.1":
        return svc.execute_appointment_reminder_workflow(appt_id)

    elif req.workflow_code == "20.2":
        return svc.execute_questionnaire_reminder_workflow(
            appointment_id=appt_id,
            questionnaire_id=req.questionnaire_id or "Q-INTAKE-01"
        )

    elif req.workflow_code == "20.3":
        return svc.execute_failed_booking_workflow(
            appointment_id=appt_id,
            simulated_retry_success=req.simulated_retry_success
        )

    elif req.workflow_code == "20.4":
        sess = req.session_id or "SESSION-DEMO-204"
        return svc.execute_human_escalation_workflow(
            session_id=sess,
            reason=req.reason or "PATIENT_EXPLICIT_REQUEST_HUMAN"
        )

    elif req.workflow_code == "20.5":
        return svc.execute_appointment_cancellation_workflow(appointment_id=appt_id)

    elif req.workflow_code == "20.6":
        return svc.execute_appointment_rescheduling_workflow(
            appointment_id=appt_id,
            new_start_datetime=req.new_start_datetime
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow code '{req.workflow_code}'. Valid codes: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6"
        )
