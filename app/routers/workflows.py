"""
Background Asynchronous Workflow Engine Router (Section 5.28).
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.workflows.engine import BackgroundWorkflowEngine
from app.database.models import WorkflowInstance, WorkflowStepLog, Appointment, Doctor, Hospital, WorkflowStatus

router = APIRouter(prefix="/api/v1/workflows", tags=["Background Asynchronous Workflows"])


class TriggerWorkflowInput(BaseModel):
    workflow_name: str  # APPOINTMENT_REMINDER_WORKFLOW, QUESTIONNAIRE_REMINDER_WORKFLOW, FAILED_BOOKING_RECOVERY_WORKFLOW, POST_BOOKING_WORKFLOW
    appointment_id: str
    delay_minutes: Optional[int] = 1440
    questionnaire_id: Optional[str] = None
    error_reason: Optional[str] = None


@router.post("/trigger")
def trigger_background_workflow(payload: TriggerWorkflowInput, db: Session = Depends(get_db)):
    engine = BackgroundWorkflowEngine(db)
    wname = payload.workflow_name.upper().strip()

    if wname == "APPOINTMENT_REMINDER_WORKFLOW":
        wf = engine.start_appointment_reminder_workflow(payload.appointment_id, delay_minutes=payload.delay_minutes or 1440)
    elif wname == "QUESTIONNAIRE_REMINDER_WORKFLOW":
        wf = engine.start_questionnaire_reminder_workflow(payload.appointment_id, payload.questionnaire_id or "Q-1")
    elif wname == "FAILED_BOOKING_RECOVERY_WORKFLOW":
        wf = engine.start_failed_booking_recovery_workflow(payload.appointment_id, payload.error_reason or "EHR connection timed out")
    elif wname == "POST_BOOKING_WORKFLOW":
        wf = engine.start_post_booking_workflow(payload.appointment_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported workflow name '{payload.workflow_name}'")

    return {
        "workflow_id": wf.id,
        "workflow_name": wf.workflow_name,
        "status": wf.status.value,
        "appointment_id": wf.appointment_id,
        "scheduled_for": wf.scheduled_for.isoformat() if wf.scheduled_for else None
    }

@router.post("/execute-due")
def execute_due_scheduled_workflows(db: Session = Depends(get_db)):
    engine = BackgroundWorkflowEngine(db)
    executed_count = engine.execute_due_scheduled_workflows()
    return {"executed_due_workflows": executed_count}

@router.get("/instances")
def list_workflow_instances(
    status: Optional[str] = None,
    hospital_id: Optional[str] = Query(None, description="Optional hospital filter"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(WorkflowInstance)
    if hospital_id:
        query = query.outerjoin(Appointment, WorkflowInstance.appointment_id == Appointment.id).filter(
            (Appointment.hospital_id == hospital_id) | (WorkflowInstance.payload_json.contains(hospital_id))
        )
    if status:
        query = query.filter(WorkflowInstance.status == status.upper())
    instances = query.order_by(WorkflowInstance.created_at.desc()).limit(limit).all()

    # Calculate status counts
    base_q = db.query(WorkflowInstance)
    if hospital_id:
        base_q = base_q.outerjoin(Appointment, WorkflowInstance.appointment_id == Appointment.id).filter(
            (Appointment.hospital_id == hospital_id) | (WorkflowInstance.payload_json.contains(hospital_id))
        )
    all_instances = base_q.all()
    status_counts = {
        "total": len(all_instances),
        "waiting": sum(1 for w in all_instances if getattr(w.status, 'value', str(w.status)) == "WAITING"),
        "running": sum(1 for w in all_instances if getattr(w.status, 'value', str(w.status)) == "RUNNING"),
        "completed": sum(1 for w in all_instances if getattr(w.status, 'value', str(w.status)) == "COMPLETED"),
        "failed": sum(1 for w in all_instances if getattr(w.status, 'value', str(w.status)) == "FAILED"),
        "escalated": sum(1 for w in all_instances if getattr(w.status, 'value', str(w.status)) == "ESCALATED"),
    }

    res_list = []
    for wf in instances:
        appt = db.query(Appointment).filter(Appointment.id == wf.appointment_id).first() if wf.appointment_id else None
        hosp = db.query(Hospital).filter(Hospital.id == appt.hospital_id).first() if appt and appt.hospital_id else None
        doc = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first() if appt and appt.doctor_id else None

        res_list.append({
            "workflow_id": wf.id,
            "workflow_name": wf.workflow_name,
            "trigger_event": wf.trigger_event,
            "status": wf.status.value if hasattr(wf.status, "value") else str(wf.status),
            "appointment_id": wf.appointment_id,
            "patient_name": appt.patient_name if appt else None,
            "doctor_name": doc.name if doc else None,
            "hospital_name": hosp.name if hosp else None,
            "hospital_id": hosp.id if hosp else (appt.hospital_id if appt else None),
            "scheduled_for": wf.scheduled_for.isoformat() if wf.scheduled_for else None,
            "created_at": wf.created_at.isoformat() if hasattr(wf, "created_at") and wf.created_at else None
        })

    return {
        "total": len(instances),
        "status_counts": status_counts,
        "instances": res_list
    }


@router.get("/instances/{instance_id}")
def get_workflow_instance_history(instance_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    logs = db.query(WorkflowStepLog).filter(WorkflowStepLog.workflow_id == instance_id).all()
    
    return {
        "workflow_id": wf.id,
        "workflow_name": wf.workflow_name,
        "trigger_event": wf.trigger_event,
        "status": wf.status.value,
        "scheduled_for": wf.scheduled_for.isoformat() if wf.scheduled_for else None,
        "step_logs": [
            {
                "step_name": l.step_name,
                "step_status": l.step_status,
                "attempt_count": l.attempt_count,
                "message": l.message,
                "timestamp": l.timestamp.isoformat()
            } for l in logs
        ]
    }

