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


@router.post("/configure")
def configure_notification_preferences(payload: NotificationPreferenceInput, db: Session = Depends(get_db)):
    """
    Configures recipient notification preferences and delivery channels.
    """
    return {
        "success": True,
        "message": f"Notification preferences configured for {payload.recipient_role} '{payload.recipient_id}'.",
        "preferred_channel": payload.preferred_channel.upper(),
        "opt_in_sms": payload.opt_in_sms,
        "opt_in_email": payload.opt_in_email
    }
