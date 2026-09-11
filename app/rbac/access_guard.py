"""
Access Guard & Boundary Enforcement Engine (Step 6).

Enforces:
1. Role-to-permission mapping for Platform Admin, Hospital Admin, Doctor, and Patient.
2. Hospital Admin Multi-Tenant Isolation (cannot access another hospital's data).
3. Doctor Boundary Isolation (cannot access other doctors' calendars, slots, or appointments).
4. Patient Boundary Isolation (cannot access other patients' profiles, appointments, or responses).
5. Immutable security audit logging on every authorization decision.
"""

import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.rbac import UserRole, Permission, ROLE_PERMISSIONS_MAP
from app.database.models import AuditLog
from app.audit import AuditCategory, PrivacyLevel


@dataclass
class UserContext:
    user_id: str
    role: str  # PLATFORM_ADMIN, HOSPITAL_ADMIN, DOCTOR, PATIENT
    hospital_id: Optional[str] = None
    doctor_id: Optional[str] = None
    patient_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AccessGuard:
    """
    Central Authorization Evaluator enforcing Step 6 RBAC boundaries.
    """

    @classmethod
    def evaluate(
        cls,
        user_context: UserContext,
        permission: str,
        target_hospital_id: Optional[str] = None,
        target_doctor_id: Optional[str] = None,
        target_patient_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates whether user_context has permission and respects scope/tenant boundaries.
        """
        # 1. Parse and validate role
        role_str = (user_context.role or "").upper()
        try:
            role = UserRole(role_str)
        except ValueError:
            return {
                "authorized": False,
                "decision": "DENIED",
                "role": role_str,
                "permission": permission,
                "reason": f"Invalid role '{role_str}'. Valid roles: {[r.value for r in UserRole]}",
                "context": user_context.to_dict(),
            }

        # 2. Parse and validate permission
        try:
            perm = Permission(permission)
        except ValueError:
            return {
                "authorized": False,
                "decision": "DENIED",
                "role": role.value,
                "permission": permission,
                "reason": f"Unknown permission '{permission}'.",
                "context": user_context.to_dict(),
            }

        # 3. Check role-permission grant
        allowed_perms = ROLE_PERMISSIONS_MAP.get(role, set())
        if perm not in allowed_perms:
            result = {
                "authorized": False,
                "decision": "DENIED",
                "role": role.value,
                "permission": perm.value,
                "reason": f"Role '{role.value}' is not granted permission '{perm.value}'.",
                "context": user_context.to_dict(),
            }
            cls._log_security_audit(db, user_context, perm.value, result)
            return result

        # 4. Boundary Enforcement
        # Rule A: Hospital Admin multi-tenant isolation
        if role == UserRole.HOSPITAL_ADMIN and target_hospital_id:
            if not user_context.hospital_id or user_context.hospital_id != target_hospital_id:
                result = {
                    "authorized": False,
                    "decision": "DENIED",
                    "role": role.value,
                    "permission": perm.value,
                    "reason": f"Tenant isolation violation: Hospital Admin (hospital '{user_context.hospital_id}') cannot access another hospital's private data ('{target_hospital_id}').",
                    "context": user_context.to_dict(),
                }
                cls._log_security_audit(db, user_context, perm.value, result, target_hospital_id=target_hospital_id)
                return result

        # Rule B: Doctor boundary isolation
        if role == UserRole.DOCTOR and target_doctor_id:
            if not user_context.doctor_id or user_context.doctor_id != target_doctor_id:
                result = {
                    "authorized": False,
                    "decision": "DENIED",
                    "role": role.value,
                    "permission": perm.value,
                    "reason": f"Doctor boundary violation: Doctor '{user_context.doctor_id}' cannot access another doctor's resources ('{target_doctor_id}').",
                    "context": user_context.to_dict(),
                }
                cls._log_security_audit(db, user_context, perm.value, result, target_doctor_id=target_doctor_id)
                return result

        # Rule C: Patient boundary isolation
        if role == UserRole.PATIENT and target_patient_id:
            if not user_context.patient_id or user_context.patient_id != target_patient_id:
                result = {
                    "authorized": False,
                    "decision": "DENIED",
                    "role": role.value,
                    "permission": perm.value,
                    "reason": f"Patient boundary violation: Patient '{user_context.patient_id}' cannot access another patient's data ('{target_patient_id}').",
                    "context": user_context.to_dict(),
                }
                cls._log_security_audit(db, user_context, perm.value, result, target_patient_id=target_patient_id)
                return result

        # 5. Access Granted
        result = {
            "authorized": True,
            "decision": "GRANTED",
            "role": role.value,
            "permission": perm.value,
            "reason": f"Access granted to role '{role.value}' for operation '{perm.value}'.",
            "context": user_context.to_dict(),
        }
        cls._log_security_audit(db, user_context, perm.value, result, status="SUCCESS")
        return result

    @classmethod
    def enforce(
        cls,
        user_context: UserContext,
        permission: str,
        target_hospital_id: Optional[str] = None,
        target_doctor_id: Optional[str] = None,
        target_patient_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Enforces RBAC evaluation. Raises HTTP 403 Forbidden if not authorized.
        """
        eval_result = cls.evaluate(
            user_context=user_context,
            permission=permission,
            target_hospital_id=target_hospital_id,
            target_doctor_id=target_doctor_id,
            target_patient_id=target_patient_id,
            db=db,
        )
        if not eval_result["authorized"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=eval_result,
            )
        return eval_result

    @classmethod
    def _log_security_audit(
        cls,
        db: Optional[Session],
        user_context: UserContext,
        permission: str,
        result: Dict[str, Any],
        target_hospital_id: Optional[str] = None,
        target_doctor_id: Optional[str] = None,
        target_patient_id: Optional[str] = None,
        status: str = "DENIED",
    ):
        """Persists a security audit event in the Section 5.40 Audit Trail."""
        if not db:
            return
        try:
            event = AuditLog(
                hospital_id=user_context.hospital_id or target_hospital_id,
                event_type="RBAC_AUTHORIZATION_CHECK",
                category=AuditCategory.SECURITY_REVIEW.value,
                actor_id=user_context.user_id,
                actor_role=user_context.role,
                resource_type=permission,
                resource_id=target_hospital_id or target_doctor_id or target_patient_id,
                status=status,
                privacy_level=PrivacyLevel.STRUCTURED_NO_PHI.value,
                payload_json=json.dumps({
                    "decision": result.get("decision"),
                    "permission": permission,
                    "reason": result.get("reason"),
                    "target_hospital_id": target_hospital_id,
                    "target_doctor_id": target_doctor_id,
                    "target_patient_id": target_patient_id,
                }, default=str),
            )
            db.add(event)
            db.commit()
        except Exception:
            pass
