"""
Hospital Onboarding & Platform Admin Approval Router.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.onboarding.hospital_onboarding import (
    HospitalSelfServiceOnboardingService, DraftHospitalInput, InitialAdminCredentials, EHRIntegrationConfigInput
)
from app.admin.admin_approval import PlatformAdminApprovalService

router = APIRouter(prefix="/api/v1/onboarding", tags=["Hospital Onboarding & Admin Approval"])


class RejectHospitalInput(BaseModel):
    reason: str

class RequestCorrectionsInput(BaseModel):
    notes: str

class SuspendHospitalInput(BaseModel):
    reason: str


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
    hosp = onboarding.reject_hospital(hospital_id, payload.reason)
    return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "rejection_reason": hosp.rejection_reason}


# Platform Admin Review Endpoints
admin_router = APIRouter(prefix="/api/v1/admin/hospitals", tags=["Platform Admin Approval"])

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
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.post("/{hospital_id}/reject")
def admin_reject_hospital(hospital_id: str, payload: RejectHospitalInput, db: Session = Depends(get_db)):
    admin_service = PlatformAdminApprovalService(db)
    try:
        hosp = admin_service.reject_hospital(hospital_id, payload.reason)
        return {"hospital_id": hosp.id, "status": hosp.hospital_status.value, "is_active": hosp.is_active, "rejection_reason": hosp.rejection_reason}
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
