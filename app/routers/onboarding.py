"""
Hospital Onboarding & Platform Admin Approval Router.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.onboarding.hospital_onboarding import (
    HospitalSelfServiceOnboardingService, DraftHospitalInput, InitialAdminCredentials, EHRIntegrationConfigInput
)
from app.admin.admin_approval import PlatformAdminApprovalService

router = APIRouter(prefix="/api/v1/onboarding", tags=["Hospital Onboarding & Admin Approval"])


class RejectHospitalInput(BaseModel):
    reason: Optional[str] = None
    rejection_reason: Optional[str] = None

    @property
    def effective_reason(self) -> str:
        return self.reason or self.rejection_reason or "Application rejected by Platform Super-Admin"

class RequestCorrectionsInput(BaseModel):
    notes: str

class SuspendHospitalInput(BaseModel):
    reason: str

class HospitalRegistrationRequest(BaseModel):
    name: str = Field(..., description="Hospital Name")
    code: str = Field(..., description="Hospital Short Code e.g. CITYMEM")
    contact_email: str = Field(..., description="Facility Contact Email")
    admin_name: str = Field(..., description="Facility Administrator Full Name")
    admin_email: str = Field(..., description="Facility Administrator Email")
    admin_password: Optional[str] = Field(None, description="Initial administrator password")
    phone: Optional[str] = None
    address: Optional[str] = None
    organization_info: Optional[str] = None
    departments: Optional[List[str]] = []
    specialties: Optional[List[str]] = []


@router.post("/register")
def register_new_hospital(payload: HospitalRegistrationRequest, db: Session = Depends(get_db)):
    """
    Submits a new hospital registration request.
    Places the facility into SUBMITTED status (is_active = False), awaiting platform admin approval.
    Also provisions the hospital admin user account in an inactive state until approved.
    """
    from app.database.models import Hospital, HospitalStatus, UserAccount
    import json
    from app.auth.auth_service import hash_password

    clean_code = payload.code.strip().upper()
    existing_code = db.query(Hospital).filter(Hospital.code == clean_code).first()
    if existing_code:
        raise HTTPException(status_code=400, detail=f"A hospital with code '{clean_code}' already exists.")

    existing_email = db.query(Hospital).filter(Hospital.contact_email == payload.contact_email.strip().lower()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail=f"A hospital application with email '{payload.contact_email}' is already registered.")

    hosp = Hospital(
        name=payload.name.strip(),
        code=clean_code,
        contact_email=payload.contact_email.strip().lower(),
        phone=payload.phone.strip() if payload.phone else None,
        address=payload.address.strip() if payload.address else None,
        organization_info=payload.organization_info.strip() if payload.organization_info else None,
        admin_name=payload.admin_name.strip(),
        admin_email=payload.admin_email.strip().lower(),
        departments_json=json.dumps(payload.departments) if payload.departments else "[]",
        specialties_json=json.dumps(payload.specialties) if payload.specialties else "[]",
        hospital_status=HospitalStatus.SUBMITTED,
        is_active=False
    )
    db.add(hosp)
    db.commit()
    db.refresh(hosp)

    # Prepare inactive UserAccount for the facility admin
    admin_email_clean = payload.admin_email.strip().lower()
    user = db.query(UserAccount).filter(UserAccount.email == admin_email_clean).first()
    if not user:
        user = UserAccount(
            email=admin_email_clean,
            full_name=payload.admin_name.strip(),
            password_hash=hash_password(payload.admin_password or "demo123"),
            role="HOSPITAL_ADMIN",
            hospital_id=hosp.id,
            hospital_name=hosp.name,
            auth_provider="LOCAL",
            is_active=False  # Inactive until platform admin approves the hospital!
        )
        db.add(user)
        db.commit()
    else:
        user.hospital_id = hosp.id
        user.hospital_name = hosp.name
        user.role = "HOSPITAL_ADMIN"
        user.full_name = payload.admin_name.strip()
        if payload.admin_password:
            user.password_hash = hash_password(payload.admin_password)
        user.is_active = False
        db.commit()

    return {
        "status": "success",
        "is_pending_approval": True,
        "message": f"Hospital registration for '{hosp.name}' submitted successfully. It is now awaiting approval from the Platform Super-Admin.",
        "hospital_id": hosp.id,
        "hospital_name": hosp.name,
        "hospital_code": hosp.code,
        "admin_name": hosp.admin_name,
        "admin_email": hosp.admin_email,
        "hospital": {
            "id": hosp.id,
            "hospital_id": hosp.id,
            "name": hosp.name,
            "code": hosp.code,
            "contact_email": hosp.contact_email,
            "admin_name": hosp.admin_name,
            "admin_email": hosp.admin_email,
            "departments": payload.departments or [],
            "status": hosp.hospital_status.value,
            "hospital_status": hosp.hospital_status.value,
            "is_active": hosp.is_active
        }
    }


@router.post("/draft")
def create_draft_hospital(payload: DraftHospitalInput, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.create_draft_hospital(
        name=payload.name,
        code=payload.code,
        contact_email=payload.contact_email,
        admin_name=payload.admin_name,
        admin_email=payload.admin_email
    )
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "code": hosp.code}

@router.get("/{hospital_id}")
def get_hospital(hospital_id: str, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.get_hospital(hospital_id)
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return {
        "id": hosp.id,
        "name": hosp.name,
        "code": hosp.code,
        "status": hosp.hospital_status.value,
        "is_active": hosp.is_active,
        "profile_completed": hosp.profile_completed
    }

@router.post("/{hospital_id}/credentials")
def set_admin_credentials(hospital_id: str, payload: InitialAdminCredentials, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.set_admin_credentials(hospital_id, payload.admin_name, payload.admin_email)
    return {"hospital_id": hosp.id, "admin_email": hosp.admin_email}

@router.post("/{hospital_id}/ehr-config")
def set_ehr_config(hospital_id: str, payload: EHRIntegrationConfigInput, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    config = onboarding.configure_ehr_integration(
        hospital_id=hospital_id,
        adapter_type=payload.adapter_type,
        api_base_url=payload.api_base_url,
        api_key=payload.api_key,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        tenant_id=payload.tenant_id,
        is_ehr_authoritative=payload.is_ehr_authoritative,
        ehr_vendor_name=payload.ehr_vendor_name
    )
    return {"hospital_id": hospital_id, "ehr_config_id": config.id, "adapter_type": config.adapter_type.value}

@router.post("/{hospital_id}/submit")
def submit_application(hospital_id: str, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.submit_application(hospital_id)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value}

@router.post("/{hospital_id}/approve")
def approve_hospital(hospital_id: str, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.approve_hospital(hospital_id)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}

@router.post("/{hospital_id}/reject")
def reject_hospital(hospital_id: str, payload: RejectHospitalInput, db: Session = Depends(get_db)):
    onboarding = HospitalSelfServiceOnboardingService(db)
    hosp = onboarding.reject_hospital(hospital_id, payload.effective_reason)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "rejection_reason": hosp.rejection_reason}


# Platform Admin Review Endpoints
admin_router = APIRouter(prefix="/api/v1/admin/hospitals", tags=["Platform Admin Approval"])

@admin_router.get("")
@admin_router.get("/")
def admin_list_hospitals(
    status: Optional[str] = Query(None, description="Optional status filter: PENDING, SUBMITTED, APPROVED, REJECTED"),
    db: Session = Depends(get_db)
):
    """
    Returns list of all hospital registration requests, with aggregate counters for pending, approved, and rejected applications.
    """
    admin_service = PlatformAdminApprovalService(db)
    return admin_service.list_hospital_applications(status_filter=status)


@admin_router.get("/{hospital_id}")
def admin_review_hospital_info(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        return admin_service.review_hospital_info(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@admin_router.post("/{hospital_id}/approve")
def admin_approve_hospital(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.approve_hospital(hospital_id)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "hospital_status": hosp.hospital_status.value, "is_active": hosp.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.post("/{hospital_id}/reject")
def admin_reject_hospital(hospital_id: str, payload: RejectHospitalInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.reject_hospital(hospital_id, payload.effective_reason)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "hospital_status": hosp.hospital_status.value, "is_active": hosp.is_active, "rejection_reason": hosp.rejection_reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.post("/{hospital_id}/request-corrections")
def admin_request_corrections(hospital_id: str, payload: RequestCorrectionsInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.request_corrections(hospital_id, payload.notes)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "correction_notes": hosp.correction_notes}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.post("/{hospital_id}/suspend")
def admin_suspend_hospital(hospital_id: str, payload: SuspendHospitalInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.suspend_hospital(hospital_id, payload.reason)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "suspension_reason": hosp.suspension_reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.post("/{hospital_id}/reactivate")
def admin_reactivate_hospital(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.reactivate_hospital(hospital_id)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.get("/{hospital_id}/activity")
def admin_view_hospital_activity(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        return admin_service.view_hospital_activity(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@admin_router.get("/{hospital_id}/ehr-config")
def admin_review_ehr_config(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        return admin_service.review_ehr_integration_config(hospital_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@admin_router.post("/{hospital_id}/ehr-config/activate")
def admin_activate_ehr_config(hospital_id: str, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        config = admin_service.activate_ehr_integration(hospital_id)
        return {"hospital_id": hospital_id, "config_id": config.id, "is_active": config.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
