"""
Doctor Dashboard Service (Section 5.31).

Provides clinical dashboard capabilities for doctors:
1. Home Overview:
   - Today's appointments
   - Upcoming appointments
   - Pending pre-visit questionnaires
   - Recently completed questionnaires
2. Calendar Management:
   - Day, Week, and Month views
   - Multiple Calendars support
   - Booked slots, Available slots, Blocked slots, and Leave entries
3. 360-Degree Appointment Details:
   - Patient info (Name, Phone, Email, Language)
   - Appointment & Hospital info
   - Pre-visit questionnaire responses
   - Relevant authorized clinical context & interaction notes
   - External EHR appointment reference ID
"""

import json
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    Doctor, Hospital, Appointment, AppointmentStatus, PatientProfile, BlockedSlot,
    DoctorLeave, DoctorCalendar, PatientIntakeRecord, PatientQuestionnaireResponse, EHRMapping
)
from app.scheduling.availability_engine import AvailabilityEngine


class DoctorDashboardService:
    """
    Service layer executing Doctor Dashboard telemetry, multi-view calendar queries,
    and 360-degree appointment detail resolution.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.availability_engine = AvailabilityEngine(db_session)

    # -------------------------------------------------------------------------
    # 1. HOME SUMMARY VIEW
    # -------------------------------------------------------------------------
    def get_home_summary(self, doctor_id: str) -> Dict[str, Any]:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError(f"Doctor '{doctor_id}' not found.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Today's Appointments
        todays_appts = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.start_datetime >= today_start,
            Appointment.start_datetime <= today_end,
            Appointment.status != AppointmentStatus.CANCELLED
        ).order_by(Appointment.start_datetime.asc()).all()

        # Upcoming Appointments (after today)
        upcoming_appts = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.start_datetime > today_end,
            Appointment.status != AppointmentStatus.CANCELLED
        ).order_by(Appointment.start_datetime.asc()).limit(10).all()

        # Pre-visit Questionnaires (Completed vs Pending)
        completed_intakes = self.db.query(PatientIntakeRecord).join(Appointment).filter(
            Appointment.doctor_id == doctor_id
        ).order_by(PatientIntakeRecord.created_at.desc()).limit(10).all()

        pending_questionnaires = []
        for appt in todays_appts + upcoming_appts:
            intake = self.db.query(PatientIntakeRecord).filter(PatientIntakeRecord.appointment_id == appt.id).first()
            if not intake:
                pending_questionnaires.append({
                    "appointment_id": appt.id,
                    "patient_name": appt.patient_name,
                    "start_datetime": appt.start_datetime.isoformat(),
                    "status": "PENDING_INTAKE"
                })

        return {
            "doctor_id": doc.id,
            "doctor_name": doc.name,
            "specialty": doc.specialty,
            "summary_counts": {
                "todays_appointments_count": len(todays_appts),
                "upcoming_appointments_count": len(upcoming_appts),
                "pending_questionnaires_count": len(pending_questionnaires),
                "completed_questionnaires_count": len(completed_intakes)
            },
            "todays_appointments": [
                {
                    "id": a.id,
                    "patient_name": a.patient_name,
                    "patient_phone": a.patient_phone,
                    "start_datetime": a.start_datetime.isoformat(),
                    "end_datetime": a.end_datetime.isoformat(),
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                    "is_ehr_verified": a.is_ehr_verified
                }
                for a in todays_appts
            ],
            "upcoming_appointments": [
                {
                    "id": a.id,
                    "patient_name": a.patient_name,
                    "start_datetime": a.start_datetime.isoformat(),
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status)
                }
                for a in upcoming_appts
            ],
            "pending_questionnaires": pending_questionnaires,
            "recently_completed_questionnaires": [
                {
                    "intake_id": i.id,
                    "appointment_id": i.appointment_id,
                    "summary": i.patient_reported_summary,
                    "submitted_at": i.created_at.isoformat()
                }
                for i in completed_intakes
            ]
        }

    # -------------------------------------------------------------------------
    # 2. CALENDAR MANAGEMENT VIEW (Day, Week, Month, Multiple Calendars)
    # -------------------------------------------------------------------------
    def get_calendar_view(
        self,
        doctor_id: str,
        view_type: str = "DAY",
        target_date_str: Optional[str] = None,
        calendar_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError(f"Doctor '{doctor_id}' not found.")

        target_d = datetime.fromisoformat(target_date_str).date() if target_date_str else date.today()

        # Date Boundaries
        if view_type.upper() == "DAY":
            start_dt = datetime.combine(target_d, datetime.min.time())
            end_dt = datetime.combine(target_d, datetime.max.time())
        elif view_type.upper() == "WEEK":
            start_d = target_d - timedelta(days=target_d.weekday())
            end_d = start_d + timedelta(days=6)
            start_dt = datetime.combine(start_d, datetime.min.time())
            end_dt = datetime.combine(end_d, datetime.max.time())
        elif view_type.upper() == "MONTH":
            start_d = target_d.replace(day=1)
            next_month = (start_d + timedelta(days=32)).replace(day=1)
            end_d = next_month - timedelta(days=1)
            start_dt = datetime.combine(start_d, datetime.min.time())
            end_dt = datetime.combine(end_d, datetime.max.time())
        else:
            start_dt = datetime.combine(target_d, datetime.min.time())
            end_dt = datetime.combine(target_d, datetime.max.time())

        # Multiple Calendars
        calendars = self.db.query(DoctorCalendar).filter(DoctorCalendar.doctor_id == doctor_id).all()
        if calendar_ids:
            calendars = [c for c in calendars if c.id in calendar_ids]

        # Booked Slots (Appointments)
        appt_query = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.start_datetime >= start_dt,
            Appointment.end_datetime <= end_dt,
            Appointment.status != AppointmentStatus.CANCELLED
        )
        if calendar_ids:
            appt_query = appt_query.filter(Appointment.calendar_id.in_(calendar_ids))

        booked_appts = appt_query.all()

        # Blocked Slots
        blocked_slots = self.db.query(BlockedSlot).filter(
            BlockedSlot.doctor_id == doctor_id,
            BlockedSlot.start_datetime >= start_dt,
            BlockedSlot.end_datetime <= end_dt
        ).all()

        # Doctor Leave Records
        leaves = self.db.query(DoctorLeave).filter(
            DoctorLeave.doctor_id == doctor_id,
            DoctorLeave.start_date <= end_dt.date(),
            DoctorLeave.end_date >= start_dt.date()
        ).all()

        # Calculate Available Slots
        avail_slots = self.availability_engine.query_actual_availability(
            doctor_id=doctor_id,
            target_date=target_d,
            time_window="ANYTIME"
        )


        return {
            "doctor_id": doctor_id,
            "view_type": view_type.upper(),
            "target_date": target_d.isoformat(),
            "date_range": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            },
            "calendars": [
                {
                    "id": c.id,
                    "name": c.calendar_name,
                    "type": c.calendar_type.value if hasattr(c.calendar_type, 'value') else str(c.calendar_type)
                }
                for c in calendars
            ],
            "booked_slots": [
                {
                    "appointment_id": a.id,
                    "patient_name": a.patient_name,
                    "start_datetime": a.start_datetime.isoformat(),
                    "end_datetime": a.end_datetime.isoformat(),
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status)
                }
                for a in booked_appts
            ],
            "available_slots": avail_slots,
            "blocked_slots": [
                {
                    "id": b.id,
                    "start_datetime": b.start_datetime.isoformat(),
                    "end_datetime": b.end_datetime.isoformat(),
                    "reason": b.reason
                }
                for b in blocked_slots
            ],
            "leaves": [
                {
                    "id": l.id,
                    "leave_type": l.leave_type,
                    "start_date": l.start_date.isoformat(),
                    "end_date": l.end_date.isoformat(),
                    "reason": l.reason,
                    "status": l.status
                }
                for l in leaves
            ]
        }

    # -------------------------------------------------------------------------
    # 3. 360-DEGREE APPOINTMENT DETAILS VIEW
    # -------------------------------------------------------------------------
    def get_appointment_details(self, doctor_id: str, appointment_id: str) -> Dict[str, Any]:
        appt = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.doctor_id == doctor_id
        ).first()

        if not appt:
            raise ValueError(f"Appointment '{appointment_id}' not found for doctor '{doctor_id}'.")

        hosp = self.db.query(Hospital).filter(Hospital.id == appt.hospital_id).first()
        doc = self.db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()

        # Patient Profile & Notes
        patient_profile = None
        if appt.patient_phone:
            patient_profile = self.db.query(PatientProfile).filter(PatientProfile.phone_number == appt.patient_phone).first()

        # Pre-visit Questionnaire Intake
        intake_record = self.db.query(PatientIntakeRecord).filter(PatientIntakeRecord.appointment_id == appointment_id).first()

        # External EHR Reference
        ehr_map = self.db.query(EHRMapping).filter(
            EHRMapping.internal_id == appointment_id,
            EHRMapping.entity_type == "APPOINTMENT"
        ).first()

        return {
            "appointment_id": appt.id,
            "patient": {
                "id": patient_profile.id if patient_profile else None,
                "name": appt.patient_name,
                "phone_number": appt.patient_phone,
                "email": appt.patient_email,
                "preferred_language": patient_profile.preferred_language if patient_profile else "English",
                "external_patient_id": patient_profile.external_patient_id if patient_profile else None
            },
            "appointment": {
                "id": appt.id,
                "start_datetime": appt.start_datetime.isoformat(),
                "end_datetime": appt.end_datetime.isoformat(),
                "status": appt.status.value if hasattr(appt.status, 'value') else str(appt.status),
                "consultation_type": doc.consultation_type.value if (doc and hasattr(doc.consultation_type, 'value')) else "IN_PERSON",
                "duration_minutes": doc.default_appointment_duration if doc else 30,
                "is_ehr_verified": appt.is_ehr_verified
            },
            "hospital": {
                "id": hosp.id if hosp else None,
                "name": hosp.name if hosp else "Unknown Hospital",
                "code": hosp.code if hosp else "",
                "timezone": hosp.timezone if hosp else "UTC"
            },
            "pre_visit_questionnaire": {
                "has_submitted": intake_record is not None,
                "patient_reported_symptoms": intake_record.patient_reported_summary if intake_record else "No pre-visit questionnaire submitted yet.",
                "intake_answers": json.loads(intake_record.intake_answers_json) if (intake_record and intake_record.intake_answers_json) else {},
                "encryption_status": intake_record.encryption_status if intake_record else "N/A"
            },
            "relevant_authorized_context": {
                "interaction_notes": patient_profile.interaction_notes if patient_profile else "No prior interaction notes recorded.",
                "preferred_time_window": patient_profile.preferred_time_window.value if (patient_profile and hasattr(patient_profile.preferred_time_window, 'value')) else "ANYTIME",
                "privacy_guardrail_applied": "PHI anonymized at telemetry boundaries."
            },
            "external_ehr_reference": ehr_map.external_ehr_id if ehr_map else (appt.external_ehr_id if hasattr(appt, 'external_ehr_id') else None)
        }

    # -------------------------------------------------------------------------
    # 4. LEAVE MANAGEMENT
    # -------------------------------------------------------------------------
    def create_doctor_leave(
        self,
        doctor_id: str,
        start_date: date,
        end_date: date,
        leave_type: str = "ANNUAL_LEAVE",
        reason: Optional[str] = None
    ) -> DoctorLeave:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError(f"Doctor '{doctor_id}' not found.")

        leave = DoctorLeave(
            doctor_id=doctor_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            reason=reason or "Scheduled Doctor Leave"
        )
        self.db.add(leave)
        
        # Block calendar slots automatically for leave duration
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        blocked = BlockedSlot(
            doctor_id=doctor_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            reason=f"ON_LEAVE: {leave_type}"
        )
        self.db.add(blocked)
        self.db.commit()

        return leave

    def get_doctor_leaves(self, doctor_id: str) -> List[DoctorLeave]:
        return self.db.query(DoctorLeave).filter(DoctorLeave.doctor_id == doctor_id).order_by(DoctorLeave.start_date.desc()).all()
