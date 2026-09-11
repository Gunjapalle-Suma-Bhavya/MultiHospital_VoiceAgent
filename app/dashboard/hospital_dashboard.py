"""
Hospital Administrator Dashboard Service (Section 5.32).

Provides organization-specific dashboard capabilities for hospital administrators:
1. 13 Core KPIs:
   - Appointments today
   - Upcoming appointments
   - Active doctors count
   - Available slots count
   - Cancelled appointments count
   - Rescheduled appointments count
   - AI bookings count
   - Human escalations count
   - Questionnaire completion count & %
   - Workflow failures count
   - EHR integration success count
   - EHR integration failures count
   - Reconciliation items count
2. 10 Management Domains:
   - Departments, Specialties, Doctors, Calendars, Availability, Questionnaires, Staff, Workflows, Communication Settings, EHR Integrations
"""

import json
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    Hospital, Doctor, DoctorStatus, DoctorCalendar, Appointment, AppointmentStatus,
    HospitalQuestionnaire, HospitalStaff, HospitalOperationalPreference, EHRIntegrationConfig,
    WorkflowInstance, WorkflowStatus, EHRSyncLog, PatientIntakeRecord, AuditLog, AITelemetryLog
)
from app.scheduling.availability_engine import AvailabilityEngine


class HospitalDashboardService:
    """
    Organization-specific dashboard service for hospital administrators.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.availability_engine = AvailabilityEngine(db_session)

    def get_hospital_kpis(self, hospital_id: str) -> Dict[str, Any]:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError(f"Hospital '{hospital_id}' not found.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 1. Appointments Today
        appts_today = self.db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.start_datetime >= today_start,
            Appointment.start_datetime <= today_end,
            Appointment.status != AppointmentStatus.CANCELLED
        ).all()

        # 2. Upcoming Appointments
        appts_upcoming = self.db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.start_datetime > today_end,
            Appointment.status != AppointmentStatus.CANCELLED
        ).all()

        # 3. Active Doctors
        active_doctors = self.db.query(Doctor).filter(
            Doctor.hospital_id == hospital_id,
            Doctor.is_active == True,
            Doctor.doctor_status == DoctorStatus.ACTIVE
        ).all()

        # 4. Available Slots Today
        total_available_slots = 0
        for doc in active_doctors:
            slots = self.availability_engine.query_actual_availability(
                doctor_id=doc.id,
                target_date=now.date(),
                time_window="ANYTIME"
            )
            total_available_slots += len(slots)

        # 5. Cancelled Appointments
        cancelled_appts = self.db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.status == AppointmentStatus.CANCELLED
        ).all()

        # 6. Rescheduled Appointments
        rescheduled_appts = self.db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.status == AppointmentStatus.RESCHEDULED
        ).all()

        # 7. AI Bookings
        ai_bookings = self.db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.is_ehr_verified == True
        ).all()

        # 8. Human Escalations
        human_escalations = self.db.query(AuditLog).filter(
            AuditLog.hospital_id == hospital_id,
            AuditLog.event_type == "ESCALATE_TO_HUMAN"
        ).all()

        # 9. Questionnaire Completion
        intakes = self.db.query(PatientIntakeRecord).join(Appointment).filter(
            Appointment.hospital_id == hospital_id
        ).all()
        total_bookings_count = len(appts_today) + len(appts_upcoming)
        completion_pct = round((len(intakes) / total_bookings_count * 100.0), 1) if total_bookings_count > 0 else 100.0

        # 10. Workflow Failures
        workflow_failures = self.db.query(WorkflowInstance).join(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            WorkflowInstance.status.in_([WorkflowStatus.FAILED, WorkflowStatus.ESCALATED])
        ).all()

        # 11. EHR Integration Success
        ehr_successes = self.db.query(EHRSyncLog).filter(
            EHRSyncLog.hospital_id == hospital_id,
            EHRSyncLog.sync_status == "VERIFIED"
        ).all()

        # 12. EHR Integration Failures
        ehr_failures = self.db.query(EHRSyncLog).filter(
            EHRSyncLog.hospital_id == hospital_id,
            EHRSyncLog.sync_status == "FAILED"
        ).all()

        # 13. Reconciliation Items
        reconciliations = self.db.query(Appointment).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.status.in_([
                AppointmentStatus.RECONCILIATION_REQUIRED,
                AppointmentStatus.PENDING_EHR_VERIFICATION,
                AppointmentStatus.SYNCHRONIZATION_PENDING
            ])
        ).all()

        return {
            "hospital_id": hosp.id,
            "hospital_name": hosp.name,
            "hospital_code": hosp.code,
            "status": hosp.hospital_status.value if hasattr(hosp.hospital_status, 'value') else str(hosp.hospital_status),
            "kpis": {
                "appointments_today": len(appts_today),
                "upcoming_appointments": len(appts_upcoming),
                "active_doctors": len(active_doctors),
                "available_slots_today": total_available_slots,
                "cancelled_appointments": len(cancelled_appts),
                "rescheduled_appointments": len(rescheduled_appts),
                "ai_bookings": len(ai_bookings),
                "human_escalations": len(human_escalations),
                "questionnaires_completed": len(intakes),
                "questionnaire_completion_percentage": completion_pct,
                "workflow_failures": len(workflow_failures),
                "ehr_integration_success": len(ehr_successes),
                "ehr_integration_failures": len(ehr_failures),
                "reconciliation_items": len(reconciliations)
            }
        }

    def get_management_overview(self, hospital_id: str) -> Dict[str, Any]:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError(f"Hospital '{hospital_id}' not found.")

        # Departments & Specialties
        departments = json.loads(hosp.departments_json) if hosp.departments_json else ["General Medicine", "Cardiology", "Pediatrics", "Diagnostics"]
        specialties = json.loads(hosp.specialties_json) if hosp.specialties_json else ["Cardiology", "Neurology", "Pediatrics", "Internal Medicine"]

        # Doctors & Calendars
        doctors = self.db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()
        doc_ids = [d.id for d in doctors]
        calendars = self.db.query(DoctorCalendar).filter(DoctorCalendar.doctor_id.in_(doc_ids)).all() if doc_ids else []

        # Questionnaires & Staff
        questionnaires = self.db.query(HospitalQuestionnaire).filter(HospitalQuestionnaire.hospital_id == hospital_id).all()
        staff = self.db.query(HospitalStaff).filter(HospitalStaff.hospital_id == hospital_id).all()

        # Workflows
        workflows = self.db.query(WorkflowInstance).join(Appointment).filter(Appointment.hospital_id == hospital_id).limit(10).all()

        # Operational Preferences & EHR Config
        pref = self.db.query(HospitalOperationalPreference).filter(HospitalOperationalPreference.hospital_id == hospital_id).first()
        ehr_cfg = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()

        return {
            "hospital_id": hosp.id,
            "hospital_name": hosp.name,
            "management": {
                "departments": departments,
                "specialties": specialties,
                "doctors": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "specialty": d.specialty,
                        "department": d.department,
                        "status": d.doctor_status.value if hasattr(d.doctor_status, 'value') else str(d.doctor_status)
                    }
                    for d in doctors
                ],
                "calendars": [
                    {
                        "id": c.id,
                        "doctor_id": c.doctor_id,
                        "calendar_name": c.calendar_name,
                        "calendar_type": c.calendar_type.value if hasattr(c.calendar_type, 'value') else str(c.calendar_type)
                    }
                    for c in calendars
                ],
                "availability": {
                    "operating_hours": json.loads(hosp.operating_hours_json) if hosp.operating_hours_json else "Mon-Fri: 8:00 AM - 5:00 PM",
                    "max_advance_booking_days": pref.max_advance_booking_days if pref else 30
                },
                "questionnaires": [
                    {
                        "id": q.id,
                        "title": q.title,
                        "specialty": q.specialty,
                        "is_approved": q.is_approved_by_clinician
                    }
                    for q in questionnaires
                ],
                "staff": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "email": s.email,
                        "role": s.role
                    }
                    for s in staff
                ],
                "workflows": [
                    {
                        "id": w.id,
                        "workflow_name": w.workflow_name,
                        "status": w.status.value if hasattr(w.status, 'value') else str(w.status)
                    }
                    for w in workflows
                ],
                "communication_settings": {
                    "communication_preference": pref.communication_preference if pref else "VOICE_AND_SMS",
                    "auto_reminders_enabled": pref.auto_reminders_enabled if pref else True,
                    "sms_enabled": pref.sms_enabled if pref else True,
                    "voice_enabled": pref.voice_enabled if pref else True
                },
                "healthcare_system_integrations": {
                    "adapter_type": ehr_cfg.adapter_type.value if (ehr_cfg and hasattr(ehr_cfg.adapter_type, 'value')) else "MOCK_EHR",
                    "endpoint_url": ehr_cfg.endpoint_url if ehr_cfg else "https://fhir.mock-ehr.org/r4",
                    "is_sync_enabled": ehr_cfg.is_sync_enabled if ehr_cfg else True,
                    "require_external_verification": ehr_cfg.require_external_verification if ehr_cfg else True
                }
            }
        }
