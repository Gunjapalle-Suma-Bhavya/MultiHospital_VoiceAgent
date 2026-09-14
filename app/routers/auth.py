"""
Authentication and Role-Based User Management REST API.

Provides endpoints for:
- User registration with role selection and hospital affiliation
- Local credential authentication (Email/Phone + Password)
- Google OAuth Sign-Up & Sign-In integration
- Hospital listing for registration and login selection
- Current user profile session resolution (/me)
- Demo personas quick authentication
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.auth.auth_service import AuthService
from app.database.models import UserAccount

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Identity"])


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class SignUpRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=4, description="User password")
    full_name: str = Field(..., description="User's full name")
    role: str = Field("PATIENT", description="One of: PATIENT, DOCTOR, HOSPITAL_STAFF, HOSPITAL_ADMIN, PLATFORM_ADMIN")
    hospital_id: Optional[str] = Field(None, description="Affiliated Hospital ID if hospital staff/admin/doctor")
    phone_number: Optional[str] = Field(None, description="Contact phone number")
    specialty: Optional[str] = Field(None, description="Doctor medical specialty")
    department: Optional[str] = Field(None, description="Doctor clinical department")
    qualifications: Optional[str] = Field(None, description="Doctor qualifications/degrees")
    experience_years: Optional[int] = Field(None, description="Years of medical practice experience")
    bio: Optional[str] = Field(None, description="Doctor bio or clinical focus")


class LoginRequest(BaseModel):
    email_or_identifier: Optional[str] = Field(None, description="Email address or phone number")
    identifier: Optional[str] = Field(None, description="Alias for email_or_identifier")
    password: Optional[str] = Field(None, description="Password (optional for demo accounts)")
    role: Optional[str] = Field(None, description="Optional role hint for demo accounts")
    hospital_id: Optional[str] = Field(None, description="Selected Hospital ID for hospital staff/admin")


class GoogleAuthRequest(BaseModel):
    google_id: str = Field(..., description="Google Subject/User ID or unique sub token")
    email: str = Field(..., description="Google verified email address")
    name: str = Field(..., description="User's full name from Google profile")
    avatar_url: Optional[str] = Field(None, description="Google profile picture URL")
    role: str = Field("PATIENT", description="Role selected by user: PATIENT, DOCTOR, HOSPITAL_STAFF, HOSPITAL_ADMIN, PLATFORM_ADMIN")
    hospital_id: Optional[str] = Field(None, description="Hospital ID if role requires facility affiliation")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/hospitals")
def get_hospitals_directory(db: Session = Depends(get_db)):
    """
    Returns accredited hospital facilities for the role-selection dropdown.
    """
    auth_service = AuthService(db)
    return {
        "status": "success",
        "hospitals": auth_service.list_hospitals()
    }


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def register_account(payload: SignUpRequest, db: Session = Depends(get_db)):
    """
    Registers a new user account with role selection and hospital linkage.
    """
    auth_service = AuthService(db)
    try:
        session_data = auth_service.register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            hospital_id=payload.hospital_id,
            phone_number=payload.phone_number,
            auth_provider="LOCAL",
            specialty=payload.specialty,
            department=payload.department,
            qualifications=payload.qualifications,
            experience_years=payload.experience_years,
            bio=payload.bio
        )
        is_pending = session_data.get("is_pending_approval", False)
        msg = session_data.get("message") or f"Account successfully created as {payload.role}."
        return {
            "status": "pending_approval" if is_pending else "success",
            "message": msg,
            "session": session_data if not is_pending else None,
            "is_pending_approval": is_pending,
            **session_data
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(err)}")


@router.get("/doctor-status/{doctor_id}")
def get_doctor_registration_status(doctor_id: str, db: Session = Depends(get_db)):
    """
    Checks the real-time approval and credentialing status of a doctor.
    If approved and active, automatically provisions and returns the active user session.
    """
    from app.database.models import Doctor, DoctorStatus, Hospital, UserAccount

    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor registration request '{doctor_id}' not found."
        )

    hosp = db.query(Hospital).filter(Hospital.id == doc.hospital_id).first()
    hosp_name = hosp.name if hosp else "Affiliated Hospital"

    # Check if approved
    if doc.doctor_status == DoctorStatus.ACTIVE and doc.is_active:
        user = db.query(UserAccount).filter(UserAccount.doctor_id == doc.id).first()
        if not user:
            user = db.query(UserAccount).filter(UserAccount.email == doc.id).first()

        auth_service = AuthService(db)
        session_data = None
        if user:
            user.is_active = True
            db.commit()
            session_data = auth_service.create_session_for_user(user)

        return {
            "status": "APPROVED",
            "is_approved": True,
            "doctor_status": "ACTIVE",
            "is_active": True,
            "doctor_id": doc.id,
            "hospital_id": doc.hospital_id,
            "hospital_name": hosp_name,
            "name": doc.name,
            "specialty": doc.specialty,
            "department": doc.department,
            "qualifications": doc.qualifications,
            "experience_years": doc.experience_years,
            "bio": doc.bio,
            "message": f"Dr. {doc.name} has been approved and credentialed by {hosp_name}.",
            "session": session_data,
            "user": session_data
        }

    elif doc.doctor_status == DoctorStatus.PENDING_APPROVAL:
        return {
            "status": "PENDING_APPROVAL",
            "is_approved": False,
            "doctor_status": "PENDING_APPROVAL",
            "is_active": False,
            "doctor_id": doc.id,
            "hospital_id": doc.hospital_id,
            "hospital_name": hosp_name,
            "name": doc.name,
            "specialty": doc.specialty,
            "department": doc.department,
            "qualifications": doc.qualifications,
            "experience_years": doc.experience_years,
            "bio": doc.bio,
            "message": f"Please wait for {hosp_name} administrator to approve your credentials."
        }

    else:
        return {
            "status": "REJECTED",
            "is_approved": False,
            "doctor_status": doc.doctor_status.value if hasattr(doc.doctor_status, 'value') else str(doc.doctor_status),
            "is_active": False,
            "doctor_id": doc.id,
            "hospital_id": doc.hospital_id,
            "hospital_name": hosp_name,
            "name": doc.name,
            "message": doc.special_instructions or f"Registration request for {doc.name} was rejected or deactivated."
        }


@router.get("/hospital-status/{hospital_id}")
def get_hospital_registration_status(hospital_id: str, db: Session = Depends(get_db)):
    """
    Checks the real-time approval and accreditation status of a hospital.
    If approved and active, automatically provisions and returns the active session.
    """
    from app.database.models import Hospital, HospitalStatus, UserAccount
    import json

    hosp = db.query(Hospital).filter(
        (Hospital.id == hospital_id) | (Hospital.code == hospital_id.upper())
    ).first()
    if not hosp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital registration request '{hospital_id}' not found."
        )

    depts = []
    if hosp.departments_json:
        try:
            depts = json.loads(hosp.departments_json)
        except Exception:
            pass

    # Check if approved
    if hosp.hospital_status == HospitalStatus.APPROVED and hosp.is_active:
        user = db.query(UserAccount).filter(
            (UserAccount.hospital_id == hosp.id) & (UserAccount.role == "HOSPITAL_ADMIN")
        ).first()
        if not user and hosp.admin_email:
            user = db.query(UserAccount).filter(UserAccount.email == hosp.admin_email.strip().lower()).first()

        auth_service = AuthService(db)
        session_data = None
        if user:
            user.is_active = True
            user.hospital_name = hosp.name
            db.commit()
            session_data = auth_service.create_session_for_user(user)
        elif hosp.admin_email:
            from app.auth.auth_service import hash_password
            user = UserAccount(
                email=hosp.admin_email.strip().lower(),
                full_name=hosp.admin_name or f"{hosp.name} Administrator",
                password_hash=hash_password("demo123"),
                role="HOSPITAL_ADMIN",
                hospital_id=hosp.id,
                hospital_name=hosp.name,
                auth_provider="LOCAL",
                is_active=True
            )
            db.add(user)
            db.commit()
            session_data = auth_service.create_session_for_user(user)

        return {
            "status": "APPROVED",
            "is_approved": True,
            "hospital_status": "APPROVED",
            "is_active": True,
            "hospital_id": hosp.id,
            "hospital_name": hosp.name,
            "code": hosp.code,
            "contact_email": hosp.contact_email,
            "admin_name": hosp.admin_name,
            "admin_email": hosp.admin_email,
            "departments": depts,
            "message": f"Hospital '{hosp.name}' has been approved and accredited by the Platform Super-Admin.",
            "session": session_data,
            "user": session_data
        }

    elif hosp.hospital_status in (HospitalStatus.SUBMITTED, HospitalStatus.UNDER_REVIEW, HospitalStatus.DRAFT):
        return {
            "status": "PENDING_APPROVAL",
            "is_approved": False,
            "hospital_status": hosp.hospital_status.value,
            "is_active": False,
            "hospital_id": hosp.id,
            "hospital_name": hosp.name,
            "code": hosp.code,
            "contact_email": hosp.contact_email,
            "admin_name": hosp.admin_name,
            "admin_email": hosp.admin_email,
            "departments": depts,
            "message": f"Please wait for the Platform Super-Admin to approve facility registration for '{hosp.name}'."
        }

    elif hosp.hospital_status == HospitalStatus.CORRECTION_REQUESTED:
        return {
            "status": "CORRECTION_REQUESTED",
            "is_approved": False,
            "hospital_status": "CORRECTION_REQUESTED",
            "is_active": False,
            "hospital_id": hosp.id,
            "hospital_name": hosp.name,
            "code": hosp.code,
            "correction_notes": hosp.correction_notes,
            "message": f"Corrections requested by Platform Super-Admin: {hosp.correction_notes}"
        }

    else:
        return {
            "status": "REJECTED",
            "is_approved": False,
            "hospital_status": hosp.hospital_status.value if hasattr(hosp.hospital_status, 'value') else str(hosp.hospital_status),
            "is_active": False,
            "hospital_id": hosp.id,
            "hospital_name": hosp.name,
            "code": hosp.code,
            "rejection_reason": hosp.rejection_reason,
            "message": hosp.rejection_reason or f"Hospital registration request for '{hosp.name}' was rejected or deactivated."
        }


@router.post("/login")
def login_account(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates an existing user account or seamlessly logs in demo personas.
    """
    valid_roles = ["PATIENT", "DOCTOR", "HOSPITAL_STAFF", "HOSPITAL_ADMIN", "PLATFORM_ADMIN"]
    if payload.role and payload.role.upper() not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of {valid_roles}"
        )

    ident = (payload.email_or_identifier or payload.identifier or "").strip()
    if not ident:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email_or_identifier or identifier is required"
        )

    auth_service = AuthService(db)
    try:
        session_data = auth_service.authenticate_local(
            email_or_identifier=ident,
            password=payload.password,
            role_hint=payload.role,
            hospital_id=payload.hospital_id
        )
        return {
            "status": "success",
            "message": "Authentication successful.",
            "session": session_data,
            "user": session_data,
            **session_data
        }
    except ValueError as err:
        err_str = str(err)
        from app.database.models import Hospital, UserAccount, Doctor
        # Check for hospital pending approval
        if "awaiting approval from the System Admin" in err_str or "inactive" in err_str.lower():
            target_hosp = None
            if payload.hospital_id:
                target_hosp = db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
            if not target_hosp:
                u = db.query(UserAccount).filter(UserAccount.email == payload.email_or_identifier.strip().lower()).first()
                if u and u.hospital_id:
                    target_hosp = db.query(Hospital).filter(Hospital.id == u.hospital_id).first()
            if target_hosp:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": err_str,
                        "is_pending_approval": True,
                        "hospital_id": target_hosp.id,
                        "hospital_name": target_hosp.name,
                        "hospital_code": target_hosp.code,
                        "role": "HOSPITAL_ADMIN"
                    }
                )
        # Check for doctor pending approval
        if "awaiting credentialing and approval by the Hospital Administrator" in err_str:
            u = db.query(UserAccount).filter(UserAccount.email == payload.email_or_identifier.strip().lower()).first()
            doc_id = u.doctor_id if u else None
            h_id = u.hospital_id if u else payload.hospital_id
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": err_str,
                    "is_pending_approval": True,
                    "doctor_id": doc_id,
                    "hospital_id": h_id,
                    "role": "DOCTOR"
                }
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err_str)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Authentication failed: {str(err)}")


@router.post("/google")
def authenticate_with_google(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticates or provisions a user account via Google OAuth.
    Assigns the user-selected role and hospital affiliation.
    """
    valid_roles = ["PATIENT", "DOCTOR", "HOSPITAL_STAFF", "HOSPITAL_ADMIN", "PLATFORM_ADMIN"]
    if payload.role and payload.role.upper() not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of {valid_roles}"
        )

    auth_service = AuthService(db)
    try:
        session_data = auth_service.authenticate_google(
            email=payload.email,
            full_name=payload.name,
            google_id=payload.google_id,
            avatar_url=payload.avatar_url,
            role=payload.role,
            hospital_id=payload.hospital_id
        )
        return {
            "status": "success",
            "message": "Google authentication successful.",
            "session": session_data,
            **session_data
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Google OAuth failed: {str(err)}")


@router.get("/me")
def get_current_user_profile(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """
    Returns session and profile details for the currently active user.
    """
    auth_service = AuthService(db)
    if authorization:
        session = auth_service.get_session_by_token(authorization)
        if session:
            return {"status": "success", "user": session}

    if x_user_id and x_user_id != "user-anonymous":
        user = db.query(UserAccount).filter(UserAccount.id == x_user_id).first()
        if user:
            from app.rbac import UserRole, ROLE_PERMISSIONS_MAP
            role_enum = UserRole(user.role) if user.role in UserRole._value2member_map_ else UserRole.PATIENT
            perms = list(ROLE_PERMISSIONS_MAP.get(role_enum, []))
            return {
                "status": "success",
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "full_name": user.full_name,
                    "name": user.full_name,
                    "role": user.role,
                    "hospital_id": user.hospital_id,
                    "hospital_name": user.hospital_name,
                    "doctor_id": user.doctor_id,
                    "patient_id": user.patient_id,
                    "auth_provider": user.auth_provider,
                    "avatar_url": user.avatar_url,
                    "permissions": [p.value for p in perms]
                }
            }

    # Fallback to guest session
    return {
        "status": "guest",
        "user": {
            "user_id": "guest",
            "role": x_user_role or "PATIENT",
            "full_name": "Guest Visitor",
            "permissions": []
        }
    }


@router.post("/logout")
def logout_account():
    """
    Logs out the current user and clears session tokens.
    """
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/users")
def list_platform_users(
    role: Optional[str] = Query(None, description="Optional role filter"),
    hospital_id: Optional[str] = Query(None, description="Optional hospital filter"),
    db: Session = Depends(get_db)
):
    """
    Lists registered user accounts for the Platform Admin User Authentication & RBAC board.
    """
    query = db.query(UserAccount)
    if role and role.upper() != "ALL":
        query = query.filter(UserAccount.role == role.upper())
    if hospital_id:
        query = query.filter(UserAccount.hospital_id == hospital_id)

    users = query.order_by(UserAccount.created_at.desc()).all()

    return {
        "status": "success",
        "total_count": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "hospital_id": u.hospital_id,
                "hospital_name": u.hospital_name,
                "auth_provider": u.auth_provider,
                "is_active": bool(u.is_active),
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]
    }


@router.post("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: str, db: Session = Depends(get_db)):
    """
    Toggles user active state (activation / deactivation).
    """
    user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    user.is_active = not bool(user.is_active)
    db.commit()
    db.refresh(user)

    # Sync to MongoDB Atlas if available
    try:
        from app.database.mongodb import persist_to_mongodb
        persist_to_mongodb("users", {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "hospital_id": user.hospital_id,
            "is_active": user.is_active
        }, key_field="id")
    except Exception:
        pass

    return {
        "status": "success",
        "user_id": user.id,
        "is_active": user.is_active,
        "message": f"User account is now {'active' if user.is_active else 'deactivated'}."
    }
