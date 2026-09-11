"""
Notification System REST API Router (Section 5.30).
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.notifications.notification_engine import NotificationEngine
from app.database.models import NotificationRecord


router = APIRouter(prefix="/api/v1/notifications", tags=["Notification System"])


class SendNotificationInput(BaseModel):
    recipient_role: str  # PATIENT, DOCTOR, HOSPITAL
    recipient_id: str
    notification_type: str
    body: str
    subject: Optional[str] = None
    channel: str = "SMS"
    metadata: Optional[Dict[str, Any]] = None


class NotificationPreferenceInput(BaseModel):
    recipient_role: str
    recipient_id: str
    preferred_channel: str = "SMS"
    opt_in_sms: bool = True
    opt_in_email: bool = True


@router.post("/send")
def send_notification(payload: SendNotificationInput, db: Session = Depends(get_db)):
    """
    Sends a configurable notification to a Patient, Doctor, or Hospital.
    """
    engine = NotificationEngine(db)
    record = engine.send_notification(
        recipient_role=payload.recipient_role.upper(),
        recipient_id=payload.recipient_id,
        notification_type=payload.notification_type,
        body=payload.body,
        subject=payload.subject,
        channel=payload.channel.upper(),
        metadata=payload.metadata
    )
    try:
        from app.database.mongodb import persist_to_mongodb
        persist_to_mongodb("notifications", {
            "notification_id": record.id,
            "recipient_role": record.recipient_role,
            "recipient_id": record.recipient_id,
            "notification_type": record.notification_type,
            "channel": record.channel,
            "body": record.body,
            "status": record.status,
            "sent_at": record.sent_at.isoformat() if record.sent_at else None
        }, key_field="notification_id")
    except Exception:
        pass
    return {
        "success": True,
        "notification_id": record.id,
        "recipient_role": record.recipient_role,
        "recipient_id": record.recipient_id,
        "notification_type": record.notification_type,
        "channel": record.channel,
        "status": record.status,
        "sent_at": record.sent_at.isoformat() if record.sent_at else None
    }


@router.get("/recipient/{role}/{recipient_id}")
def get_recipient_notifications(role: str, recipient_id: str, db: Session = Depends(get_db)):
    """
    Queries notification logs for a specific Patient, Doctor, or Hospital recipient.
    """
    engine = NotificationEngine(db)
    records = engine.get_recipient_notifications(role.upper(), recipient_id)
    return {
        "recipient_role": role.upper(),
        "recipient_id": recipient_id,
        "count": len(records),
        "notifications": [
            {
                "id": r.id,
                "notification_type": r.notification_type,
                "channel": r.channel,
                "subject": r.subject,
                "body": r.body,
                "status": r.status,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None
            }
            for r in records
        ]
    }


@router.get("/catalog")
def get_notification_catalog():
    """
    Returns the complete catalog of configurable notifications across all 3 roles (Section 14 / Section 5.30).
    """
    return {
        "HOSPITAL": [
            {"type": "HOSPITAL_APPROVED", "title": "Hospital approved", "description": "Alert when hospital registration is approved and active."},
            {"type": "HOSPITAL_REJECTED", "title": "Hospital rejected", "description": "Alert when hospital application is rejected with cause."},
            {"type": "NEW_APPOINTMENT", "title": "New appointment", "description": "Real-time notice of new patient booking created."},
            {"type": "CANCELLATION", "title": "Cancellation", "description": "Notice of appointment cancellation."},
            {"type": "RESCHEDULING", "title": "Rescheduling", "description": "Notice of appointment rescheduled."},
            {"type": "DOCTOR_STATUS_CHANGE", "title": "Doctor status change", "description": "Alert when physician availability or status changes."},
            {"type": "WORKFLOW_FAILURE", "title": "Workflow failure", "description": "High-priority alert when clinical background workflow fails."},
            {"type": "OPERATIONAL_ALERT", "title": "Operational alert", "description": "Platform or institutional capacity alert."},
            {"type": "INTEGRATION_FAILURE", "title": "Healthcare-system integration failure", "description": "Alert when EHR/FHIR sync fails or requires recovery."},
        ],
        "DOCTOR": [
            {"type": "NEW_APPOINTMENT", "title": "New appointment", "description": "Notice when a patient books a consultation slot."},
            {"type": "APPOINTMENT_CANCELLED", "title": "Appointment cancelled", "description": "Notice when a booked appointment is cancelled."},
            {"type": "APPOINTMENT_RESCHEDULED", "title": "Appointment rescheduled", "description": "Notice when an appointment is rescheduled."},
            {"type": "QUESTIONNAIRE_COMPLETED", "title": "Questionnaire completed", "description": "Alert when patient finishes pre-visit intake form."},
            {"type": "UPCOMING_APPOINTMENT", "title": "Upcoming appointment", "description": "Daily or pre-shift reminder of upcoming schedule."},
            {"type": "WORKFLOW_NOTIFICATION", "title": "Workflow notification", "description": "Clinical task, reminder, or follow-up status."},
        ],
        "PATIENT": [
            {"type": "APPOINTMENT_CONFIRMATION", "title": "Appointment confirmation", "description": "Immediate confirmation following 5-point verification."},
            {"type": "APPOINTMENT_REMINDER", "title": "Appointment reminder", "description": "24h / 2h upcoming visit reminder via SMS or voice."},
            {"type": "RESCHEDULING_CONFIRMATION", "title": "Rescheduling confirmation", "description": "Confirmation of updated date, time, and doctor."},
            {"type": "CANCELLATION_CONFIRMATION", "title": "Cancellation confirmation", "description": "Confirmation of appointment cancellation."},
            {"type": "QUESTIONNAIRE_REMINDER", "title": "Questionnaire reminder", "description": "Prompt to fill pre-visit intake questionnaire."},
            {"type": "QUESTIONNAIRE_COMPLETED", "title": "Questionnaire completion", "description": "Acknowledgment of submitted intake responses."},
            {"type": "IMPORTANT_APPOINTMENT_UPDATES", "title": "Important appointment updates", "description": "Clinic delays, room changes, or urgent preparation notices."},
        ]
    }
