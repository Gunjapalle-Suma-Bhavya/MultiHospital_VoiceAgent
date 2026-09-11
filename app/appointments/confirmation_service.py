"""
Appointment Confirmation Service (Section 5.22).

Enforces authoritative verification before generating spoken confirmation responses.
Strict Rule:
- IF is_ehr_verified == True: Return confirmed completion text ("Your appointment with Dr. Rao at City Hospital is confirmed for Thursday at 4:30 PM.").
- IF is_ehr_verified == False (or PENDING / RECONCILIATION_REQUIRED): Return pending verification text. Never communicate unverified completion.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models import Appointment, AppointmentStatus, Hospital, Doctor


class ConfirmedAppointmentDetails(BaseModel):
    appointment_id: str
    external_appointment_id: Optional[str] = None
    hospital_name: str
    doctor_name: str
    specialty: str
    date_str: str
    time_str: str
    appointment_type: str = "IN_PERSON_CONSULTATION"
    status: str
    is_verified: bool
    spoken_confirmation_text: str


class AppointmentConfirmationService:
    """
    Verified Appointment Confirmation Service (Section 5.22).
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_appointment_confirmation(self, appointment_id: str) -> ConfirmedAppointmentDetails:
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise ValueError("Appointment not found.")

        doctor = self.db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        hospital = self.db.query(Hospital).filter(Hospital.id == appt.hospital_id).first()

        doc_name = doctor.name if doctor else "Doctor"
        specialty = doctor.specialty if doctor else "General Consultation"
        hosp_name = hospital.name if hospital else "Hospital"

        # Format date & time
        dt = appt.start_datetime
        day_str = dt.strftime("%A, %B %d")
        time_str = dt.strftime("%I:%M %p").lstrip("0")

        is_verified = bool(appt.is_ehr_verified and appt.status == AppointmentStatus.SCHEDULED)

        # Enforce Section 5.22 Verification Rule
        if is_verified:
            spoken_text = (
                f"Your appointment with {doc_name} at {hosp_name} is confirmed "
                f"for {day_str} at {time_str}."
            )
        else:
            spoken_text = (
                f"Your appointment request with {doc_name} at {hosp_name} for "
                f"{day_str} at {time_str} is pending verification with the hospital system. "
                f"We will update you as soon as confirmation completes."
            )

        return ConfirmedAppointmentDetails(
            appointment_id=appt.id,
            external_appointment_id=appt.external_appointment_id,
            hospital_name=hosp_name,
            doctor_name=doc_name,
            specialty=specialty,
            date_str=day_str,
            time_str=time_str,
            appointment_type="IN_PERSON_CONSULTATION",
            status=appt.status.value,
            is_verified=is_verified,
            spoken_confirmation_text=spoken_text
        )
