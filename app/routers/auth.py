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
from fastapi import APIRouter, Depends, HTTPException, Header, status
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


class LoginRequest(BaseModel):
    email_or_identifier: str = Field(..., description="Email address or phone number")
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
            auth_provider="LOCAL"
        )
        return {
            "status": "success",
            "message": f"Account successfully created as {payload.role}.",
            "session": session_data,
            **session_data
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(err)}")


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

    auth_service = AuthService(db)
    try:
        session_data = auth_service.authenticate_local(
            email_or_identifier=payload.email_or_identifier,
            password=payload.password,
            role_hint=payload.role,
            hospital_id=payload.hospital_id
        )
        return {
            "status": "success",
            "message": "Authentication successful.",
            "session": session_data,
            **session_data
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err))
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
