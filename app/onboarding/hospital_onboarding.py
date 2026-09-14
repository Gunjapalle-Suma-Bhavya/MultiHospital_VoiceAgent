"""
Self-Service Hospital Registration & Onboarding Service (Section 5.1).

Manages hospital state machine:
Draft -> Submitted -> Under Review -> Approved / Rejected

Enforces rule: Only Approved hospitals become active (is_active = True).
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import Hospital, HospitalStatus, EHRIntegrationConfig, EHRAdapterType


class HospitalSelfServiceOnboardingService:
    """
    Manages self-service hospital registration, metadata collection, and administrative review.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_draft_hospital(
        self,
        name: str,
        code: str,
        contact_email: str,
        admin_name: str,
        admin_email: str
    ) -> Hospital:
        """
        Creates hospital application in DRAFT state. is_active = False.
        """
        hosp = Hospital(
            name=name,
            code=code,
            contact_email=contact_email,
            admin_name=admin_name,
            admin_email=admin_email,
            hospital_status=HospitalStatus.DRAFT,
            is_active=False
        )
        self.db.add(hosp)
        self.db.commit()
        return hosp

    def update_hospital_draft_metadata(
        self,
        hospital_id: str,
        organization_info: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        departments: Optional[List[str]] = None,
        specialties: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        tax_id: Optional[str] = None,
        license_id: Optional[str] = None,
        ehr_adapter_type: Optional[EHRAdapterType] = EHRAdapterType.MOCK_EHR
    ) -> Hospital:
        """
        Updates hospital metadata while in DRAFT state.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")
        if hosp.hospital_status not in [HospitalStatus.DRAFT, HospitalStatus.SUBMITTED]:
            raise ValueError(f"Cannot edit hospital metadata in state {hosp.hospital_status.value}")

        if organization_info: hosp.organization_info = organization_info
        if address: hosp.address = address
        if phone: hosp.phone = phone
        if website: hosp.website = website
        if departments: hosp.departments_json = json.dumps(departments)
        if specialties: hosp.specialties_json = json.dumps(specialties)
        if services: hosp.services_json = json.dumps(services)
        if tax_id: hosp.verification_tax_id = tax_id
        if license_id: hosp.verification_license_id = license_id

        # Update or create EHR config draft
        config = self.db.query(EHRIntegrationConfig).filter(EHRIntegrationConfig.hospital_id == hospital_id).first()
        if not config:
            config = EHRIntegrationConfig(hospital_id=hospital_id, adapter_type=ehr_adapter_type)
            self.db.add(config)
        else:
            config.adapter_type = ehr_adapter_type

        self.db.commit()
        return hosp

    def submit_application(self, hospital_id: str) -> Hospital:
        """
        Transitions DRAFT -> SUBMITTED. is_active remains False.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")
        if hosp.hospital_status != HospitalStatus.DRAFT:
            raise ValueError(f"Hospital cannot be submitted from status {hosp.hospital_status.value}")

        hosp.hospital_status = HospitalStatus.SUBMITTED
        hosp.is_active = False
        self.db.commit()
        return hosp

    def move_to_under_review(self, hospital_id: str) -> Hospital:
        """
        Transitions SUBMITTED -> UNDER_REVIEW.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        hosp.hospital_status = HospitalStatus.UNDER_REVIEW
        hosp.is_active = False
        self.db.commit()
        return hosp

    def approve_hospital(self, hospital_id: str) -> Hospital:
        """
        Transitions UNDER_REVIEW/SUBMITTED -> APPROVED.
        ENFORCEMENT: Only approved hospitals become active (is_active = True).
        """
        from datetime import datetime, timezone
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        hosp.hospital_status = HospitalStatus.APPROVED
        hosp.is_active = True  # ACTIVATED
        hosp.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Activate associated facility user accounts
        try:
            from app.database.models import UserAccount
            from app.auth.auth_service import hash_password
            admin_users = self.db.query(UserAccount).filter(UserAccount.hospital_id == hospital_id).all()
            for u in admin_users:
                u.is_active = True
                u.hospital_name = hosp.name

            if hosp.admin_email:
                adm_email = hosp.admin_email.strip().lower()
                existing_adm = self.db.query(UserAccount).filter(UserAccount.email == adm_email).first()
                if not existing_adm:
                    new_adm = UserAccount(
                        email=adm_email,
                        full_name=hosp.admin_name or f"{hosp.name} Administrator",
                        password_hash=hash_password("demo123"),
                        role="HOSPITAL_ADMIN",
                        hospital_id=hosp.id,
                        hospital_name=hosp.name,
                        auth_provider="LOCAL",
                        is_active=True
                    )
                    self.db.add(new_adm)
                else:
                    existing_adm.is_active = True
                    existing_adm.hospital_id = hosp.id
                    existing_adm.hospital_name = hosp.name
                    existing_adm.role = "HOSPITAL_ADMIN"
        except Exception:
            pass

        self.db.commit()
        return hosp

    def reject_hospital(self, hospital_id: str, reason: str) -> Hospital:
        """
        Transitions UNDER_REVIEW/SUBMITTED -> REJECTED. is_active = False.
        """
        hosp = self.db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hosp:
            raise ValueError("Hospital not found")

        hosp.hospital_status = HospitalStatus.REJECTED
        hosp.rejection_reason = reason
        hosp.is_active = False  # DEACTIVATED
        self.db.commit()
        return hosp

    def get_hospital(self, hospital_id: str) -> Optional[Hospital]:
        """
        Retrieves a hospital by ID.
        """
        return self.db.query(Hospital).filter(Hospital.id == hospital_id).first()



from pydantic import BaseModel

class DraftHospitalInput(BaseModel):
    name: str
    code: str
    contact_email: str
    admin_name: str
    admin_email: str

class InitialAdminCredentials(BaseModel):
    admin_name: str
    admin_email: str
    admin_phone: Optional[str] = None

class EHRIntegrationConfigInput(BaseModel):
    adapter_type: str = "MOCK_EHR"
    endpoint_url: Optional[str] = None
    api_base_url: Optional[str] = None
    auth_credentials: Optional[Dict[str, Any]] = None

