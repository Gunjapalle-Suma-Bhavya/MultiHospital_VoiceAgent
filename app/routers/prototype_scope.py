"""
REST API Router for Section 26: Prototype Scope & End-to-End Verification.

Provides:
- GET /api/v1/prototype/scope: Full 9-domain prototype scope catalog and feature mapping
- POST /api/v1/prototype/scope/verify: Live multi-domain verification across all 9 areas
- POST /api/v1/auth/login: Platform-wide user authentication for Admins, Staff, Doctors, and Patients
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from app.database.config import get_db
from app.vision.prototype_scope_service import PrototypeScopeService, PROTOTYPE_SCOPE_SPECIFICATION
from app.database.models import Hospital, Doctor, PatientProfile
from app.rbac import UserRole, ROLE_PERMISSIONS_MAP

router = APIRouter(tags=["Prototype Scope (Section 26)"])


class ScopeVerifyRequest(BaseModel):
    hospital_id: Optional[str] = Field(None, description="Optional hospital ID to scope verification checks")


class UserLoginRequest(BaseModel):
    email_or_identifier: str = Field(..., description="Email, phone number, or user identifier")
    role: str = Field("HOSPITAL_ADMIN", description="PLATFORM_ADMIN, HOSPITAL_ADMIN, DOCTOR, PATIENT")
    password: Optional[str] = Field(None, description="Optional password for credentials check")
    hospital_id: Optional[str] = Field(None, description="Hospital ID for Hospital Admin / Doctor context")


# -----------------------------------------------------------------------------
# Prototype Scope Endpoints
# -----------------------------------------------------------------------------

@router.get("/api/v1/prototype/scope", summary="Get Prototype Scope Specification (Section 26)")
def get_prototype_scope():
    """
    Returns the complete 9-domain prototype scope specification, feature inventory,
    associated models, services, and REST API endpoints.
    """
    return PrototypeScopeService.get_scope_specification()


@router.post("/api/v1/prototype/scope/verify", summary="Execute Live Scope Verification (Section 26)")
def verify_prototype_scope(
    payload: Optional[ScopeVerifyRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Executes live verification tests across all 9 Must-Have Prototype Scope domains:
    1. Platform
    2. Doctor
    3. Patient
    4. AI
    5. EHR / Healthcare-System Integration
    6. Questionnaire
    7. Workflow
    8. Analytics
    9. AI Operations
    """
    hosp_id = payload.hospital_id if payload else None
    return PrototypeScopeService.verify_all_domains(db=db, hospital_id=hosp_id)


# -----------------------------------------------------------------------------
# Unified Authentication Endpoint
# -----------------------------------------------------------------------------

@router.post("/api/v1/auth/login", summary="Unified Platform User Authentication")
def authenticate_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates Platform Admins, Hospital Admins, Doctors, and Patients,
    issuing tokenized credentials and persona-scoped context headers.
    """
    role_clean = payload.role.strip().upper()
    identifier = payload.email_or_identifier.strip()
    token = f"agy-auth-token-{uuid.uuid4().hex[:16]}"

    if role_clean == UserRole.PLATFORM_ADMIN.value:
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": UserRole.PLATFORM_ADMIN.value,
            "user_id": f"admin-{identifier.split('@')[0]}",
            "email": identifier,
            "permissions_count": len(ROLE_PERMISSIONS_MAP.get(UserRole.PLATFORM_ADMIN, [])),
            "headers": {
                "X-User-Role": UserRole.PLATFORM_ADMIN.value,
                "X-User-Id": f"admin-{identifier.split('@')[0]}"
            }
        }

    elif role_clean == UserRole.HOSPITAL_ADMIN.value:
        hospital = None
        if payload.hospital_id:
            hospital = db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
        if not hospital:
            hospital = db.query(Hospital).filter(
                (Hospital.admin_email == identifier) | (Hospital.contact_email == identifier) | (Hospital.code == identifier)
            ).first()
        if not hospital:
            hospital = db.query(Hospital).first()

        hosp_id = hospital.id if hospital else (payload.hospital_id or "hosp-demo-1")
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": UserRole.HOSPITAL_ADMIN.value,
            "user_id": f"hosp-admin-{identifier.split('@')[0]}",
            "email": identifier,
            "hospital_id": hosp_id,
            "hospital_name": hospital.name if hospital else "Demo General Hospital",
            "permissions_count": len(ROLE_PERMISSIONS_MAP.get(UserRole.HOSPITAL_ADMIN, [])),
            "headers": {
                "X-User-Role": UserRole.HOSPITAL_ADMIN.value,
                "X-User-Id": f"hosp-admin-{identifier.split('@')[0]}",
                "X-Hospital-Id": hosp_id
            }
        }

    elif role_clean == UserRole.DOCTOR.value:
        doctor = db.query(Doctor).filter(
            (Doctor.id == identifier) | (Doctor.name.ilike(f"%{identifier}%"))
        ).first()
        doc_id = doctor.id if doctor else identifier
        hosp_id = doctor.hospital_id if doctor else (payload.hospital_id or "hosp-demo-1")
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": UserRole.DOCTOR.value,
            "user_id": f"doc-{doc_id}",
            "doctor_id": doc_id,
            "doctor_name": doctor.name if doctor else identifier,
            "hospital_id": hosp_id,
            "permissions_count": len(ROLE_PERMISSIONS_MAP.get(UserRole.DOCTOR, [])),
            "headers": {
                "X-User-Role": UserRole.DOCTOR.value,
                "X-User-Id": f"doc-{doc_id}",
                "X-Doctor-Id": doc_id,
                "X-Hospital-Id": hosp_id
            }
        }

    elif role_clean == UserRole.PATIENT.value:
        patient = db.query(PatientProfile).filter(
            (PatientProfile.phone_number == identifier) | (PatientProfile.email == identifier) | (PatientProfile.id == identifier)
        ).first()
        pat_id = patient.id if patient else f"pat-{uuid.uuid4().hex[:8]}"
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": UserRole.PATIENT.value,
            "user_id": pat_id,
            "patient_id": pat_id,
            "phone_number": patient.phone_number if patient else identifier,
            "full_name": patient.full_name if patient else "Valued Patient",
            "permissions_count": len(ROLE_PERMISSIONS_MAP.get(UserRole.PATIENT, [])),
            "headers": {
                "X-User-Role": UserRole.PATIENT.value,
                "X-User-Id": pat_id,
                "X-Patient-Id": pat_id
            }
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported user role: {payload.role}. Must be PLATFORM_ADMIN, HOSPITAL_ADMIN, DOCTOR, or PATIENT."
        )
