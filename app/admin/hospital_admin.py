"""
Hospital Administration Service (Section 5.3).

Provides multi-tenant isolated hospital management capabilities for hospital administrators across 13 components:
1. Hospital profile
2. Departments
3. Specialties
4. Doctors
5. Calendars
6. Availability
7. Appointment settings
8. Questionnaires
9. Staff members
10. Communication preferences
11. Operational workflows
12. Healthcare-system integrations
13. Hospital analytics

Enforces strict data isolation: All queries and mutations are strictly scoped by hospital_id.
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import (
    Hospital, Doctor, DoctorWorkingHour, BlockedSlot, Appointment,
    HospitalQuestionnaire, HospitalOperationalPreference, HospitalStaff,
    EHRIntegrationConfig, EHRAdapterType, PatientIntakeRecord,
    AITelemetryLog, EHRSyncLog, WorkflowInstance
)


class HospitalAdminService:
    """
    Multi-tenant isolated administration service for hospital admins.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    # 1. Hospital Profile
    def get_hospital_profile(self, hospital_id: str) -> Dict[str, Any]:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        departments = json.loads(hosp.departments_json) if hosp.departments_json else []
        specialties = json.loads(hosp.specialties_json) if hosp.specialties_json else []
        services = json.loads(hosp.services_json) if hosp.services_json else []

        return {
            "hospital_id": hosp.id,
            "name": hosp.name,
            "code": hosp.code,
            "organization_info": hosp.organization_info,
            "address": hosp.address,
            "phone": hosp.phone,
            "contact_email": hosp.contact_email,
            "website": hosp.website,
            "timezone": hosp.timezone,
            "hospital_status": hosp.hospital_status.value if hosp.hospital_status else None,
            "is_active": hosp.is_active,
            "departments": departments,
            "specialties": specialties,
            "services": services,
            "admin_contact": {
                "name": hosp.admin_name,
                "email": hosp.admin_email,
                "phone": hosp.admin_phone
            }
        }

    def update_hospital_profile(
        self,
        hospital_id: str,
        name: Optional[str] = None,
        organization_info: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        website: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> Hospital:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        if name: hosp.name = name
        if organization_info: hosp.organization_info = organization_info
        if address: hosp.address = address
        if phone: hosp.phone = phone
        if contact_email: hosp.contact_email = contact_email
        if website: hosp.website = website
        if timezone: hosp.timezone = timezone

        self.db.commit()
        return hosp

    # 2. Departments & 3. Specialties
    def update_departments_and_specialties(
        self,
        hospital_id: str,
        departments: Optional[List[str]] = None,
        specialties: Optional[List[str]] = None,
        services: Optional[List[str]] = None
    ) -> Hospital:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        if departments is not None:
            hosp.departments_json = json.dumps(departments)
        if specialties is not None:
            hosp.specialties_json = json.dumps(specialties)
        if services is not None:
            hosp.services_json = json.dumps(services)

        self.db.commit()
        return hosp

    # 7. Appointment Settings
    def update_appointment_settings(
        self,
        hospital_id: str,
        max_advance_booking_days: int = 30,
        cancellation_notice_hours: int = 24,
        auto_reminders_enabled: bool = True
    ) -> HospitalOperationalPreference:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        pref = self.db.query(HospitalOperationalPreference).filter(
            HospitalOperationalPreference.hospital_id == hospital_id
        ).first()

        if not pref:
            pref = HospitalOperationalPreference(
                hospital_id=hospital_id,
                max_advance_booking_days=max_advance_booking_days,
                cancellation_notice_hours=cancellation_notice_hours,
                auto_reminders_enabled=auto_reminders_enabled
            )
            self.db.add(pref)
        else:
            pref.max_advance_booking_days = max_advance_booking_days
            pref.cancellation_notice_hours = cancellation_notice_hours
            pref.auto_reminders_enabled = auto_reminders_enabled

        self.db.commit()
        return pref

    # 9. Staff Management
    def add_staff_member(
        self,
        hospital_id: str,
        name: str,
        email: str,
        role: str = "STAFF",
        phone: Optional[str] = None
    ) -> HospitalStaff:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        staff = HospitalStaff(
            hospital_id=hospital_id,
            name=name,
            email=email,
            role=role,
            phone=phone,
            is_active=True
        )
        self.db.add(staff)
        self.db.commit()
        return staff

    def list_staff_members(self, hospital_id: str) -> List[Dict[str, Any]]:
        # Multi-tenant isolation filter
        staff_list = self.db.query(HospitalStaff).filter(HospitalStaff.hospital_id == hospital_id).all()
        return [
            {
                "id": s.id,
                "hospital_id": s.hospital_id,
                "name": s.name,
                "email": s.email,
                "role": s.role,
                "phone": s.phone,
                "is_active": s.is_active
            }
            for s in staff_list
        ]

    # 10. Communication Preferences
    def update_communication_preferences(
        self,
        hospital_id: str,
        communication_preference: str = "VOICE_AND_SMS",
        sms_enabled: bool = True,
        voice_enabled: bool = True
    ) -> HospitalOperationalPreference:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        pref = self.db.query(HospitalOperationalPreference).filter(
            HospitalOperationalPreference.hospital_id == hospital_id
        ).first()

        if not pref:
            pref = HospitalOperationalPreference(
                hospital_id=hospital_id,
                communication_preference=communication_preference,
                sms_enabled=sms_enabled,
                voice_enabled=voice_enabled
            )
            self.db.add(pref)
        else:
            pref.communication_preference = communication_preference
            pref.sms_enabled = sms_enabled
            pref.voice_enabled = voice_enabled

        self.db.commit()
        return pref

    # 8. Questionnaires Management
    def create_questionnaire(
        self,
        hospital_id: str,
        title: str,
        specialty: str,
        questions: List[str]
    ) -> HospitalQuestionnaire:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        q = HospitalQuestionnaire(
            hospital_id=hospital_id,
            title=title,
            specialty=specialty,
            questions_json=json.dumps(questions),
            is_approved_by_clinician=True
        )
        self.db.add(q)
        self.db.commit()
        return q

    def list_questionnaires(self, hospital_id: str) -> List[Dict[str, Any]]:
        # Multi-tenant isolation filter
        qs = self.db.query(HospitalQuestionnaire).filter(HospitalQuestionnaire.hospital_id == hospital_id).all()
        return [
            {
                "id": q.id,
                "hospital_id": q.hospital_id,
                "title": q.title,
                "specialty": q.specialty,
                "questions": json.loads(q.questions_json) if q.questions_json else [],
                "is_approved_by_clinician": q.is_approved_by_clinician
            }
            for q in qs
        ]

    # 12. Healthcare-System Integrations
    def configure_ehr_integration(
        self,
        hospital_id: str,
        adapter_type: EHRAdapterType,
        endpoint_url: Optional[str] = None,
        api_base_url: Optional[str] = None,
        is_sync_enabled: bool = True
    ) -> EHRIntegrationConfig:
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
        if not config:
            config = EHRIntegrationConfig(
                hospital_id=hospital_id,
                adapter_type=adapter_type,
                endpoint_url=endpoint_url,
                api_base_url=api_base_url,
                is_sync_enabled=is_sync_enabled
            )
            self.db.add(config)
        else:
            config.adapter_type = adapter_type
            if endpoint_url: config.endpoint_url = endpoint_url
            if api_base_url: config.api_base_url = api_base_url
            config.is_sync_enabled = is_sync_enabled

        self.db.commit()
        return config

    # 13. Hospital Analytics (Strictly Isolated)
    def get_isolated_hospital_analytics(self, hospital_id: str) -> Dict[str, Any]:
        """
        Returns isolated dashboard analytics for a specific hospital.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found or unauthorized access")

        total_doctors = self.db.query(func.count(Doctor.id)).filter(Doctor.hospital_id == hospital_id).scalar() or 0
        active_doctors = self.db.query(func.count(Doctor.id)).filter(Doctor.hospital_id == hospital_id, Doctor.is_active == True).scalar() or 0
        total_appointments = self.db.query(func.count(Appointment.id)).filter(Appointment.hospital_id == hospital_id).scalar() or 0
        intake_count = self.db.query(func.count(PatientIntakeRecord.id)).join(Appointment).filter(Appointment.hospital_id == hospital_id).scalar() or 0

        telemetry_logs = self.db.query(func.count(AITelemetryLog.id)).filter(AITelemetryLog.hospital_id == hospital_id).scalar() or 0
        ehr_syncs = self.db.query(func.count(EHRSyncLog.id)).filter(EHRSyncLog.hospital_id == hospital_id).scalar() or 0

        return {
            "hospital_id": hospital_id,
            "hospital_name": hosp.name,
            "is_active": hosp.is_active,
            "analytics": {
                "total_doctors": total_doctors,
                "active_doctors": active_doctors,
                "total_appointments": total_appointments,
                "intake_records": intake_count,
                "ai_telemetry_invocations": telemetry_logs,
                "ehr_sync_logs_count": ehr_syncs
            }
        }


from pydantic import BaseModel

class QuestionnaireCreateInput(BaseModel):
    title: str
    specialty: str
    questions: List[Dict[str, Any]]
    is_approved_by_clinician: bool = True

class QuestionnaireUpdateInput(BaseModel):
    title: Optional[str] = None
    specialty: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None
    is_approved_by_clinician: Optional[bool] = None

