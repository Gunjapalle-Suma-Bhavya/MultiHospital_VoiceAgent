"""
RBAC REST API Router (Step 6).

Exposes:
- Full RBAC matrix & role boundary definitions
- Role permission querying
- Dynamic authorization evaluation & boundary testing
- Caller permission reflection
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.rbac import (
    UserRole, Permission, ROLE_PERMISSIONS_MAP, ROLE_BOUNDARY_RULES
)
from app.rbac.access_guard import UserContext, AccessGuard
from app.rbac.dependencies import get_current_user_context

router = APIRouter(prefix="/api/v1/rbac", tags=["Role-Based Access Control (RBAC)"])


# -----------------------------------------------------------------------------
# Request Schemas
# -----------------------------------------------------------------------------
class EvaluateAccessRequest(BaseModel):
    role: str = Field(..., description="PLATFORM_ADMIN, HOSPITAL_ADMIN, DOCTOR, PATIENT")
    permission: str = Field(..., description="The operation requested")
    user_id: str = Field("user-test-01", description="ID of requesting user")
    user_hospital_id: Optional[str] = None
    user_doctor_id: Optional[str] = None
    user_patient_id: Optional[str] = None
    target_hospital_id: Optional[str] = None
    target_doctor_id: Optional[str] = None
    target_patient_id: Optional[str] = None


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/matrix")
def get_rbac_matrix():
    """
    Returns the complete Role-Based Access Control matrix for all 4 personas:
    Platform Admin (8), Hospital Admin (10), Doctor (5), and Patient (7).
    """
    matrix = {}
    for role, perms in ROLE_PERMISSIONS_MAP.items():
        meta = ROLE_BOUNDARY_RULES.get(role, {})
        matrix[role.value] = {
            "title": meta.get("title"),
            "description": meta.get("description"),
            "allowed_count": len(perms),
            "boundary_rule": meta.get("boundary_rule"),
            "permissions": sorted([p.value for p in perms]),
        }

    return {
        "roles": [r.value for r in UserRole],
        "total_roles": len(UserRole),
        "matrix": matrix,
    }


@router.get("/permissions/{role}")
def get_role_permissions(role: str):
    """
    Returns permissions and boundary rules for a specific role.
    """
    role_upper = role.upper()
    try:
        r_enum = UserRole(role_upper)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Valid roles: {[r.value for r in UserRole]}",
        )

    perms = sorted([p.value for p in ROLE_PERMISSIONS_MAP[r_enum]])
    meta = ROLE_BOUNDARY_RULES.get(r_enum, {})
    return {
        "role": r_enum.value,
        "title": meta.get("title"),
        "allowed_count": len(perms),
        "boundary_rule": meta.get("boundary_rule"),
        "permissions": perms,
    }


@router.post("/evaluate")
def evaluate_access(req: EvaluateAccessRequest, db: Session = Depends(get_db)):
    """
    Evaluates permission and tenant/doctor/patient boundary constraints without throwing 403.
    Returns structured { authorized: true/false, decision: GRANTED/DENIED, reason: ... }.
    """
    ctx = UserContext(
        user_id=req.user_id,
        role=req.role.upper(),
        hospital_id=req.user_hospital_id,
        doctor_id=req.user_doctor_id,
        patient_id=req.user_patient_id,
    )

    return AccessGuard.evaluate(
        user_context=ctx,
        permission=req.permission,
        target_hospital_id=req.target_hospital_id,
        target_doctor_id=req.target_doctor_id,
        target_patient_id=req.target_patient_id,
        db=db,
    )


@router.post("/enforce")
def enforce_access(req: EvaluateAccessRequest, db: Session = Depends(get_db)):
    """
    Strictly enforces authorization. Raises 403 Forbidden if not authorized.
    """
    ctx = UserContext(
        user_id=req.user_id,
        role=req.role.upper(),
        hospital_id=req.user_hospital_id,
        doctor_id=req.user_doctor_id,
        patient_id=req.user_patient_id,
    )

    return AccessGuard.enforce(
        user_context=ctx,
        permission=req.permission,
        target_hospital_id=req.target_hospital_id,
        target_doctor_id=req.target_doctor_id,
        target_patient_id=req.target_patient_id,
        db=db,
    )


@router.get("/me")
def get_caller_permissions(ctx: UserContext = Depends(get_current_user_context)):
    """
    Reflects the caller's context based on headers (X-User-Role, etc.) and lists granted capabilities.
    """
    try:
        r_enum = UserRole(ctx.role)
        perms = sorted([p.value for p in ROLE_PERMISSIONS_MAP[r_enum]])
    except ValueError:
        perms = []

    return {
        "context": ctx.to_dict(),
        "is_valid_role": len(perms) > 0,
        "granted_permissions_count": len(perms),
        "granted_permissions": perms,
    }
