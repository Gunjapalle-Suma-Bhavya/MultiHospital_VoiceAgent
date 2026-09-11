"""
FastAPI Dependencies for RBAC Context and Permission Enforcement (Step 6).
"""

from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.rbac import UserRole, Permission
from app.rbac.access_guard import UserContext, AccessGuard


def get_current_user_context(
    x_user_role: str = Header("PATIENT", alias="X-User-Role"),
    x_user_id: str = Header("user-anonymous", alias="X-User-Id"),
    x_hospital_id: Optional[str] = Header(None, alias="X-Hospital-Id"),
    x_doctor_id: Optional[str] = Header(None, alias="X-Doctor-Id"),
    x_patient_id: Optional[str] = Header(None, alias="X-Patient-Id"),
) -> UserContext:
    """
    Extracts the authenticated caller's UserContext from standard request headers.
    """
    return UserContext(
        user_id=x_user_id,
        role=x_user_role.upper(),
        hospital_id=x_hospital_id,
        doctor_id=x_doctor_id,
        patient_id=x_patient_id,
    )


def require_permission(permission: str):
    """
    Dependency factory ensuring the caller has the required permission.
    """
    def _dependency(
        user_context: UserContext = Depends(get_current_user_context),
        db: Session = Depends(get_db),
    ) -> UserContext:
        AccessGuard.enforce(
            user_context=user_context,
            permission=permission,
            db=db,
        )
        return user_context

    return _dependency
