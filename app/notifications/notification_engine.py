"""
Notification System (Section 5.30).

Provides configurable multi-role notifications for:
- Patient (Confirmation, Reminder, Reschedule, Cancellation, Questionnaire Reminder, Questionnaire Completion, Workflow Updates, Integration Updates)
- Doctor (New Appointment, Cancellation, Rescheduled, Questionnaire Completed, Upcoming Appointment, Operational Notifications)
- Hospital (Approval, Rejection, New Appointment, Cancellation, Rescheduling, Doctor Status Changes, Operational Alerts, Integration Failures)
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    NotificationRecord, NotificationRecipientRole, NotificationChannel, NotificationStatus
)


class NotificationEngine:
    """
    Central Notification Engine dispatching role-tailored notifications across SMS, Email, Voice, and Webhooks.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def send_notification(
        self,
        recipient_role: str,
        recipient_id: str,
        notification_type: str,
        body: str,
        subject: Optional[str] = None,
        channel: str = "SMS",
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationRecord:
        """
        Creates, formats, and persists a NotificationRecord for a recipient.
        """
        record = NotificationRecord(
            recipient_role=recipient_role,
            recipient_id=recipient_id,
            notification_type=notification_type,
            channel=channel,
            subject=subject or f"Healthcare Platform: {notification_type.replace('_', ' ').title()}",
            body=body,
            status=NotificationStatus.SENT.value,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        self.db.add(record)
        self.db.commit()
        return record

    # -------------------------------------------------------------------------
    # PATIENT NOTIFICATIONS
    # -------------------------------------------------------------------------
    def notify_patient_appointment_confirmation(self, patient_phone: str, doctor_name: str, hospital_name: str, start_dt: str) -> NotificationRecord:
        body = f"Appointment Confirmed: Your visit with {doctor_name} at {hospital_name} is scheduled for {start_dt}."
        return self.send_notification("PATIENT", patient_phone, "APPOINTMENT_CONFIRMATION", body)

    def notify_patient_appointment_reminder(self, patient_phone: str, doctor_name: str, hospital_name: str, start_dt: str) -> NotificationRecord:
        body = f"Reminder: You have an upcoming appointment with {doctor_name} at {hospital_name} on {start_dt}."
        return self.send_notification("PATIENT", patient_phone, "APPOINTMENT_REMINDER", body)

    def notify_patient_reschedule(self, patient_phone: str, doctor_name: str, hospital_name: str, new_start_dt: str) -> NotificationRecord:
        body = f"Rescheduled: Your appointment with {doctor_name} at {hospital_name} is now updated to {new_start_dt}."
        return self.send_notification("PATIENT", patient_phone, "RESCHEDULING_CONFIRMATION", body)

    def notify_patient_cancellation(self, patient_phone: str, doctor_name: str, hospital_name: str, start_dt: str) -> NotificationRecord:
        body = f"Cancelled: Your appointment with {doctor_name} at {hospital_name} for {start_dt} has been cancelled."
        return self.send_notification("PATIENT", patient_phone, "CANCELLATION_CONFIRMATION", body)

    def notify_patient_questionnaire_reminder(self, patient_phone: str, doctor_name: str) -> NotificationRecord:
        body = f"Questionnaire Pending: Please complete your pre-visit intake questionnaire for {doctor_name}."
        return self.send_notification("PATIENT", patient_phone, "QUESTIONNAIRE_REMINDER", body)

    def notify_patient_questionnaire_completion(self, patient_phone: str, doctor_name: str) -> NotificationRecord:
        body = f"Thank you! Your pre-visit questionnaire for {doctor_name} has been received and verified."
        return self.send_notification("PATIENT", patient_phone, "QUESTIONNAIRE_COMPLETED", body)

    def notify_patient_workflow_update(self, patient_phone: str, workflow_name: str, status: str) -> NotificationRecord:
        body = f"Workflow Update: Task '{workflow_name}' status is now '{status}'."
        return self.send_notification("PATIENT", patient_phone, "WORKFLOW_UPDATE", body)

    def notify_patient_integration_update(self, patient_phone: str, doctor_name: str, sync_status: str) -> NotificationRecord:
        body = f"EHR Integration Update: Verification status '{sync_status}' for appointment with {doctor_name}."
        return self.send_notification("PATIENT", patient_phone, "INTEGRATION_UPDATE", body)

    # -------------------------------------------------------------------------
    # DOCTOR NOTIFICATIONS
    # -------------------------------------------------------------------------
    def notify_doctor_new_appointment(self, doctor_id: str, patient_name: str, start_dt: str) -> NotificationRecord:
        body = f"New Appointment: Patient {patient_name} has booked a session on {start_dt}."
        return self.send_notification("DOCTOR", doctor_id, "NEW_APPOINTMENT", body)

    def notify_doctor_cancellation(self, doctor_id: str, patient_name: str, start_dt: str) -> NotificationRecord:
        body = f"Appointment Cancelled: Patient {patient_name} cancelled appointment for {start_dt}."
        return self.send_notification("DOCTOR", doctor_id, "APPOINTMENT_CANCELLATION", body)

    def notify_doctor_rescheduled(self, doctor_id: str, patient_name: str, new_start_dt: str) -> NotificationRecord:
        body = f"Appointment Rescheduled: Patient {patient_name} rescheduled to {new_start_dt}."
        return self.send_notification("DOCTOR", doctor_id, "APPOINTMENT_RESCHEDULED", body)

    def notify_doctor_questionnaire_completed(self, doctor_id: str, patient_name: str) -> NotificationRecord:
        body = f"Intake Complete: Patient {patient_name} submitted their pre-visit questionnaire."
        return self.send_notification("DOCTOR", doctor_id, "QUESTIONNAIRE_COMPLETED", body)

    def notify_doctor_upcoming_appointment(self, doctor_id: str, count: int) -> NotificationRecord:
        body = f"Schedule Reminder: You have {count} appointments scheduled for today."
        return self.send_notification("DOCTOR", doctor_id, "UPCOMING_APPOINTMENT", body)

    def notify_doctor_operational_notice(self, doctor_id: str, notice: str) -> NotificationRecord:
        body = f"Operational Notice: {notice}"
        return self.send_notification("DOCTOR", doctor_id, "OPERATIONAL_NOTIFICATION", body)

    # -------------------------------------------------------------------------
    # HOSPITAL NOTIFICATIONS
    # -------------------------------------------------------------------------
    def notify_hospital_approval(self, hospital_id: str, hospital_name: str) -> NotificationRecord:
        body = f"Hospital Approved: {hospital_name} is now approved and active on the platform."
        return self.send_notification("HOSPITAL", hospital_id, "HOSPITAL_APPROVAL", body)

    def notify_hospital_rejection(self, hospital_id: str, reason: str) -> NotificationRecord:
        body = f"Hospital Application Update: Registration status rejected. Reason: {reason}"
        return self.send_notification("HOSPITAL", hospital_id, "HOSPITAL_REJECTION", body)

    def notify_hospital_new_appointment(self, hospital_id: str, appt_id: str) -> NotificationRecord:
        body = f"Hospital Booking Alert: Appointment '{appt_id}' provisioned."
        return self.send_notification("HOSPITAL", hospital_id, "NEW_APPOINTMENT", body)

    def notify_hospital_cancellation(self, hospital_id: str, appt_id: str) -> NotificationRecord:
        body = f"Hospital Cancellation Alert: Appointment '{appt_id}' was cancelled."
        return self.send_notification("HOSPITAL", hospital_id, "CANCELLATION", body)

    def notify_hospital_rescheduling(self, hospital_id: str, appt_id: str) -> NotificationRecord:
        body = f"Hospital Reschedule Alert: Appointment '{appt_id}' was rescheduled."
        return self.send_notification("HOSPITAL", hospital_id, "RESCHEDULING", body)

    def notify_hospital_doctor_status_change(self, hospital_id: str, doctor_name: str, status: str) -> NotificationRecord:
        body = f"Doctor Status Update: Dr. {doctor_name} status is now {status}."
        return self.send_notification("HOSPITAL", hospital_id, "DOCTOR_STATUS_CHANGE", body)

    def notify_hospital_operational_alert(self, hospital_id: str, alert_msg: str) -> NotificationRecord:
        body = f"Operational Alert: {alert_msg}"
        return self.send_notification("HOSPITAL", hospital_id, "OPERATIONAL_ALERT", body)

    def notify_hospital_integration_failure(self, hospital_id: str, failure_reason: str) -> NotificationRecord:
        body = f"Integration Failure Alert: EHR connector experienced failure: {failure_reason}"
        return self.send_notification("HOSPITAL", hospital_id, "INTEGRATION_FAILURE", body)

    # -------------------------------------------------------------------------
    # QUERY NOTIFICATIONS HISTORY
    # -------------------------------------------------------------------------
    def get_recipient_notifications(self, role: str, recipient_id: str) -> List[NotificationRecord]:
        return self.db.query(NotificationRecord).filter(
            NotificationRecord.recipient_role == role,
            NotificationRecord.recipient_id == recipient_id
        ).order_by(NotificationRecord.sent_at.desc()).all()
