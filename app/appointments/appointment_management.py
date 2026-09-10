"""
Appointment Management Service (Section 5.7).

Provides full lifecycle management for appointments:
- New booking requests (REQUESTED / PENDING)
- Confirmation & Dual-State EHR Synchronization (CONFIRMED)
- Rescheduling (RESCHEDULED)
- Cancellation (CANCELLED)
- Completion (COMPLETED)
- No-Show tracking (NO_SHOW)
- Failure & Reconciliation handling (FAILED, RECONCILIATION_REQUIRED, SYNCHRONIZATION_PENDING)
- Dual-State Tracking: Internal status + External EHR status
- Appointment Change History Auditing: Logs every state transition in AppointmentStateHistory
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    Appointment, AppointmentStatus, AppointmentStateHistory, Hospital, Doctor, DoctorStatus
)
from app.scheduling.availability_engine import AvailabilityEngine
from app.ehr.integration_layer import EHRIntegrationService


class AppointmentService:
    """
    Service managing appointment lifecycle state machine, dual-state synchronization, and audit trail history.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.availability_engine = AvailabilityEngine(db_session)
        self.ehr_service = EHRIntegrationService(db_session)

    def _record_state_transition(
        self,
        appointment_id: str,
        previous_status: Optional[str],
        new_status: str,
        changed_by: str = "SYSTEM",
        reason: Optional[str] = None
    ):
        history = AppointmentStateHistory(
            appointment_id=appointment_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        self.db.add(history)
        self.db.commit()

    def create_appointment_request(
        self,
        hospital_id: str,
        doctor_id: str,
        patient_name: str,
        patient_phone: str,
        start_datetime: datetime,
        calendar_id: Optional[str] = None,
        patient_email: Optional[str] = None,
        patient_id: Optional[str] = None,
        initial_status: AppointmentStatus = AppointmentStatus.PENDING
    ) -> Appointment:
        """
        Creates appointment request after verifying 10-step slot availability pipeline.
        """
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc or doc.doctor_status != DoctorStatus.ACTIVE or not doc.is_active:
            raise ValueError("Doctor is not active or available")

        duration = doc.default_appointment_duration or 30
        end_datetime = start_datetime + timedelta(minutes=duration)

        eval_res = self.availability_engine.evaluate_slot_pipeline(
            doctor_id=doctor_id,
            slot_start=start_datetime,
            slot_end=end_datetime,
            calendar_id=calendar_id
        )

        if not eval_res["is_bookable"]:
            raise ValueError(f"Cannot request appointment: {eval_res['reason']}")

        appt = Appointment(
            hospital_id=hospital_id,
            doctor_id=doctor_id,
            calendar_id=calendar_id,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=patient_email,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            status=initial_status,
            external_status="PENDING_SYNC"
        )
        self.db.add(appt)
        self.db.commit()

        self._record_state_transition(appt.id, None, initial_status.value, changed_by="PATIENT", reason="Initial booking request created")
        return appt

    def confirm_appointment(self, appointment_id: str, changed_by: str = "SYSTEM") -> Appointment:
        """
        Confirms appointment and syncs dual-state with EHR.
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        prev = appt.status.value if appt.status else None
        appt.status = AppointmentStatus.CONFIRMED

        # Sync with external EHR adapter
        verified, msg, ext_id = self.ehr_service.sync_and_verify_booking(appointment_id)
        if verified:
            appt.status = AppointmentStatus.CONFIRMED
            appt.external_status = "EHR_CONFIRMED"
            appt.external_appointment_id = ext_id
            appt.is_ehr_verified = True
        else:
            appt.external_status = "EHR_SYNC_FAILED"
            appt.status = AppointmentStatus.RECONCILIATION_REQUIRED

        self.db.commit()
        self._record_state_transition(appt.id, prev, appt.status.value, changed_by=changed_by, reason=f"Confirmation & EHR Sync result: {msg}")
        return appt

    def reschedule_appointment(
        self,
        appointment_id: str,
        new_start_datetime: datetime,
        changed_by: str = "PATIENT",
        reason: Optional[str] = None
    ) -> Appointment:
        """
        Reschedules an appointment after evaluating availability.
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        doc = self.db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        duration = doc.default_appointment_duration if doc else 30
        new_end_datetime = new_start_datetime + timedelta(minutes=duration)

        eval_res = self.availability_engine.evaluate_slot_pipeline(
            doctor_id=appt.doctor_id,
            slot_start=new_start_datetime,
            slot_end=new_end_datetime,
            calendar_id=appt.calendar_id
        )

        if not eval_res["is_bookable"]:
            raise ValueError(f"Cannot reschedule: {eval_res['reason']}")

        prev = appt.status.value if appt.status else None
        appt.start_datetime = new_start_datetime
        appt.end_datetime = new_end_datetime
        appt.status = AppointmentStatus.RESCHEDULED
        appt.external_status = "EHR_RESCHEDULE_PENDING"

        self.db.commit()
        self._record_state_transition(appt.id, prev, AppointmentStatus.RESCHEDULED.value, changed_by=changed_by, reason=reason or "Rescheduled appointment time")
        return appt

    def cancel_appointment(
        self,
        appointment_id: str,
        changed_by: str = "PATIENT",
        reason: Optional[str] = None
    ) -> Appointment:
        """
        Cancels an appointment.
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        prev = appt.status.value if appt.status else None
        appt.status = AppointmentStatus.CANCELLED
        appt.external_status = "EHR_CANCELLED"

        self.db.commit()
        self._record_state_transition(appt.id, prev, AppointmentStatus.CANCELLED.value, changed_by=changed_by, reason=reason or "Cancelled by user")
        return appt

    def complete_appointment(self, appointment_id: str, changed_by: str = "DOCTOR") -> Appointment:
        """
        Marks appointment as COMPLETED.
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        prev = appt.status.value if appt.status else None
        appt.status = AppointmentStatus.COMPLETED
        appt.external_status = "EHR_COMPLETED"

        self.db.commit()
        self._record_state_transition(appt.id, prev, AppointmentStatus.COMPLETED.value, changed_by=changed_by, reason="Consultation finished")
        return appt

    def mark_no_show(self, appointment_id: str, changed_by: str = "CLINIC") -> Appointment:
        """
        Marks appointment as NO_SHOW.
        """
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        prev = appt.status.value if appt.status else None
        appt.status = AppointmentStatus.NO_SHOW
        appt.external_status = "EHR_NO_SHOW"

        self.db.commit()
        self._record_state_transition(appt.id, prev, AppointmentStatus.NO_SHOW.value, changed_by=changed_by, reason="Patient did not attend appointment")
        return appt

    def get_appointment_history(self, appointment_id: str) -> List[Dict[str, Any]]:
        """
        Returns full audit change log trail for an appointment.
        """
        history = self.db.query(AppointmentStateHistory).filter(
            AppointmentStateHistory.appointment_id == appointment_id
        ).order_by(AppointmentStateHistory.timestamp.asc()).all()

        return [
            {
                "id": h.id,
                "appointment_id": h.appointment_id,
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "changed_by": h.changed_by,
                "reason": h.reason,
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]
