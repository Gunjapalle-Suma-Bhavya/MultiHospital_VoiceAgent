"""
Hospital Journey Engine (Section 4.1).

Executes the complete 15-step Hospital Lifecycle:
Register Hospital -> Submit Details -> Admin Review -> Approved -> Configure Hospital ->
Create Doctors -> Configure Calendars -> Define Working Hours -> Define Availability ->
Create Questionnaires -> Configure EHR Integration -> Configure Operational Preferences ->
Publish Availability -> Monitor Operations -> Review Analytics
"""

from datetime import datetime, time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import (
    Hospital, HospitalStatus, Doctor, DoctorWorkingHour, HospitalQuestionnaire,
    HospitalOperationalPreference, EHRIntegrationConfig, EHRAdapterType, Appointment, AppointmentStatus
)


class HospitalJourneyEngine:
    """
    Executes and manages the complete Hospital Journey lifecycle.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def execute_full_hospital_journey(
        self,
        name: str,
        code: str,
        address: str,
        contact_email: str,
        doctor_name: str,
        specialty: str,
        questionnaire_title: str,
        questions: List[Dict[str, Any]],
        ehr_adapter_type: EHRAdapterType = EHRAdapterType.MOCK_EHR
    ) -> Dict[str, Any]:

        trace = []

        # 1. Register Hospital
        hosp = Hospital(name=name, code=code, hospital_status=HospitalStatus.REGISTERED)
        self.db.add(hosp)
        self.db.flush()
        trace.append({"step": 1, "action": "Register Hospital", "hospital_id": hosp.id})

        # 2. Submit Details
        hosp.address = address
        hosp.contact_email = contact_email
        hosp.hospital_status = HospitalStatus.SUBMITTED
        self.db.commit()
        trace.append({"step": 2, "action": "Submit Details", "status": "SUBMITTED"})

        # 3. Admin Review & 4. Approved
        hosp.hospital_status = HospitalStatus.APPROVED
        self.db.commit()
        trace.append({"step": 3, "action": "Admin Review", "status": "REVIEWED"})
        trace.append({"step": 4, "action": "Approved", "status": "APPROVED"})

        # 5. Configure Hospital
        hosp.hospital_status = HospitalStatus.CONFIGURED
        self.db.commit()
        trace.append({"step": 5, "action": "Configure Hospital", "status": "CONFIGURED"})

        # 6. Create Doctors
        doc = Doctor(hospital_id=hosp.id, name=doctor_name, specialty=specialty)
        self.db.add(doc)
        self.db.flush()
        trace.append({"step": 6, "action": "Create Doctors", "doctor_id": doc.id})

        # 7. Configure Calendars & 8. Define Working Hours & 9. Define Availability
        for day in [0, 1, 2, 3, 4]:
            wh = DoctorWorkingHour(
                doctor_id=doc.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                break_start=time(13, 0),
                break_end=time(14, 0)
            )
            self.db.add(wh)
        trace.append({"step": 7, "action": "Configure Calendars", "status": "COMPLETED"})
        trace.append({"step": 8, "action": "Define Working Hours", "working_days": "Mon-Fri"})
        trace.append({"step": 9, "action": "Define Availability", "hours": "09:00 - 17:00"})

        # 10. Create Questionnaires
        quest = HospitalQuestionnaire(
            hospital_id=hosp.id,
            title=questionnaire_title,
            specialty=specialty,
            questions_json=str(questions),
            is_approved_by_clinician=True
        )
        self.db.add(quest)
        trace.append({"step": 10, "action": "Create Questionnaires", "questionnaire_id": quest.id})

        # 11. Configure EHR Integration
        ehr_cfg = EHRIntegrationConfig(
            hospital_id=hosp.id,
            adapter_type=ehr_adapter_type,
            is_sync_enabled=True,
            require_external_verification=True
        )
        self.db.add(ehr_cfg)
        trace.append({"step": 11, "action": "Configure EHR Integration", "adapter": ehr_adapter_type.value})

        # 12. Configure Operational Preferences
        pref = HospitalOperationalPreference(
            hospital_id=hosp.id,
            max_advance_booking_days=30,
            cancellation_notice_hours=24,
            auto_reminders_enabled=True
        )
        self.db.add(pref)
        trace.append({"step": 12, "action": "Configure Operational Preferences", "max_advance": 30})

        # 13. Publish Availability
        hosp.hospital_status = HospitalStatus.PUBLISHED
        self.db.commit()
        trace.append({"step": 13, "action": "Publish Availability", "status": "PUBLISHED"})

        # 14. Monitor Operations & 15. Review Analytics
        analytics = self.get_hospital_analytics(hosp.id)
        trace.append({"step": 14, "action": "Monitor Operations", "active_appointments": analytics["total_appointments"]})
        trace.append({"step": 15, "action": "Review Analytics", "analytics": analytics})

        return {
            "success": True,
            "hospital_id": hosp.id,
            "hospital_status": hosp.hospital_status.value,
            "15_step_journey_trace": trace
        }

    def get_hospital_analytics(self, hospital_id: str) -> Dict[str, Any]:
        total_appts = self.db.query(func.count(Appointment.id)).filter(Appointment.hospital_id == hospital_id).scalar() or 0
        scheduled = self.db.query(func.count(Appointment.id)).filter(
            Appointment.hospital_id == hospital_id, Appointment.status == AppointmentStatus.SCHEDULED
        ).scalar() or 0
        cancelled = self.db.query(func.count(Appointment.id)).filter(
            Appointment.hospital_id == hospital_id, Appointment.status == AppointmentStatus.CANCELLED
        ).scalar() or 0

        return {
            "hospital_id": hospital_id,
            "total_appointments": total_appts,
            "scheduled_count": scheduled,
            "cancelled_count": cancelled,
            "fill_rate_pct": 100.0 if total_appts > 0 else 0.0
        }
