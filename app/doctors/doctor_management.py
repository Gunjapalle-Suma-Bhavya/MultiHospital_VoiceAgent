"""
Doctor Management Service (Section 5.4).

Manages complete doctor profile lifecycle:
- Doctor fields: Name, Photo, Specialty, Department, Qualifications, Experience, Languages, Consultation type, Duration, Hospital association, Professional info, Status, External provider identifier (EHR NPI/provider ID).
- Doctor states: INVITED, ACTIVE, INACTIVE, SUSPENDED.
- Enforces booking rule: Only ACTIVE doctors with valid availability can receive appointments.
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    Doctor, DoctorStatus, ConsultationType, Hospital, HospitalStatus,
    DoctorWorkingHour, BlockedSlot
)


class DoctorManagementService:
    """
    Service managing doctor profiles, lifecycle status transitions, and search capabilities.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def invite_doctor(
        self,
        hospital_id: str,
        name: str,
        specialty: str,
        department: Optional[str] = None,
        qualifications: Optional[str] = None,
        experience_years: int = 0,
        languages: Optional[List[str]] = None,
        consultation_type: ConsultationType = ConsultationType.IN_PERSON,
        default_appointment_duration: int = 30,
        external_provider_id: Optional[str] = None
    ) -> Doctor:
        """
        Creates doctor profile in INVITED state. is_active = False.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        doc = Doctor(
            hospital_id=hospital_id,
            name=name,
            specialty=specialty,
            department=department,
            qualifications=qualifications,
            experience_years=experience_years,
            languages_json=json.dumps(languages) if languages else json.dumps(["English"]),
            consultation_type=consultation_type,
            default_appointment_duration=default_appointment_duration,
            external_provider_id=external_provider_id,
            doctor_status=DoctorStatus.INVITED,
            is_active=False
        )
        self.db.add(doc)
        self.db.commit()
        return doc

    def activate_doctor(self, doctor_id: str) -> Doctor:
        """
        Activates doctor.
        ENFORCEMENT: Only doctors in APPROVED and active hospitals can be activated.
        """
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        hosp = self.db.query(Hospital).filter(Hospital.id == doc.hospital_id).first()
        if not hosp or hosp.hospital_status != HospitalStatus.APPROVED or not hosp.is_active:
            raise ValueError(f"Cannot activate doctor in hospital status {hosp.hospital_status.value if hosp else 'NONE'}. Only APPROVED and active hospitals can have ACTIVE doctors.")

        doc.doctor_status = DoctorStatus.ACTIVE
        doc.is_active = True
        doc.profile_completed = True
        self.db.commit()
        return doc

    def deactivate_doctor(self, doctor_id: str) -> Doctor:
        """
        Deactivates doctor (INACTIVE).
        """
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        doc.doctor_status = DoctorStatus.INACTIVE
        doc.is_active = False
        self.db.commit()
        return doc

    def suspend_doctor(self, doctor_id: str, reason: Optional[str] = None) -> Doctor:
        """
        Suspends doctor (SUSPENDED).
        """
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        doc.doctor_status = DoctorStatus.SUSPENDED
        doc.is_active = False
        if reason:
            doc.special_instructions = f"SUSPENDED: {reason}"
        self.db.commit()
        return doc

    def update_doctor_profile(
        self,
        doctor_id: str,
        name: Optional[str] = None,
        photo_url: Optional[str] = None,
        specialty: Optional[str] = None,
        department: Optional[str] = None,
        qualifications: Optional[str] = None,
        experience_years: Optional[int] = None,
        languages: Optional[List[str]] = None,
        consultation_type: Optional[ConsultationType] = None,
        default_appointment_duration: Optional[int] = None,
        external_provider_id: Optional[str] = None,
        bio: Optional[str] = None,
        professional_info: Optional[str] = None,
        special_instructions: Optional[str] = None
    ) -> Doctor:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        if name: doc.name = name
        if photo_url: doc.photo_url = photo_url
        if specialty: doc.specialty = specialty
        if department: doc.department = department
        if qualifications: doc.qualifications = qualifications
        if experience_years is not None: doc.experience_years = experience_years
        if languages: doc.languages_json = json.dumps(languages)
        if consultation_type: doc.consultation_type = consultation_type
        if default_appointment_duration: doc.default_appointment_duration = default_appointment_duration
        if external_provider_id: doc.external_provider_id = external_provider_id
        if bio: doc.bio = bio
        if professional_info: doc.professional_info = professional_info
        if special_instructions: doc.special_instructions = special_instructions

        self.db.commit()
        return doc

    def get_doctor_profile(self, doctor_id: str) -> Dict[str, Any]:
        doc = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError("Doctor not found")

        hosp = self.db.query(Hospital).filter(Hospital.id == doc.hospital_id).first()

        languages = json.loads(doc.languages_json) if doc.languages_json else []

        return {
            "doctor_id": doc.id,
            "hospital_id": doc.hospital_id,
            "hospital_name": hosp.name if hosp else "Unknown Hospital",
            "name": doc.name,
            "photo_url": doc.photo_url,
            "specialty": doc.specialty,
            "department": doc.department,
            "qualifications": doc.qualifications,
            "experience_years": doc.experience_years,
            "languages": languages,
            "consultation_type": doc.consultation_type.value if doc.consultation_type else None,
            "default_appointment_duration": doc.default_appointment_duration,
            "doctor_status": doc.doctor_status.value if doc.doctor_status else None,
            "is_active": doc.is_active,
            "external_provider_id": doc.external_provider_id,
            "bio": doc.bio,
            "professional_info": doc.professional_info,
            "profile_completed": doc.profile_completed,
            "special_instructions": doc.special_instructions
        }

    def list_doctors_for_hospital(
        self,
        hospital_id: str,
        status_filter: Optional[DoctorStatus] = None
    ) -> List[Dict[str, Any]]:
        # Multi-tenant isolation filter
        query = self.db.query(Doctor).filter(Doctor.hospital_id == hospital_id)
        if status_filter:
            query = query.filter(Doctor.doctor_status == status_filter)

        doctors = query.all()
        return [self.get_doctor_profile(d.id) for d in doctors]
