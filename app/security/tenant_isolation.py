"""
Tenant Isolation & Authorization Boundary Enforcer (Section 17).

Enforces strict tenant isolation:
- Hospital A users must not access Hospital B's private information.
- Access determined by:
  1. User role
  2. Hospital association
  3. Resource ownership
  4. Explicit permissions
- Transparent enforcement for Patients, Doctors, and Hospital Admins.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import (
    Hospital, Doctor, Appointment, PatientProfile, PrivacyAccessAudit, AuditLog
)


class TenantIsolationEnforcer:
    """
    Enforces tenant boundaries between hospitals, doctors, and patients.
    """

    @classmethod
    def verify_tenant_access(
        cls,
        db: Session,
        actor_role: str,
        actor_id: str,
        actor_hospital_id: Optional[str],
        target_hospital_id: Optional[str],
        resource_type: str,
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies that actor_hospital_id matches target_hospital_id for multi-tenant assets.
        Platform Admins have cross-hospital oversight; Hospital Admins, Doctors, and Staff are strictly isolated.
        """
        actor_role_norm = (actor_role or "PATIENT").upper()

        # Platform Admin has global oversight
        if actor_role_norm == "PLATFORM_ADMIN":
            return {
                "allowed": True,
                "reason": "Platform Admin has global authorization oversight across all tenants.",
                "actor_role": actor_role_norm,
                "target_hospital_id": target_hospital_id
            }

        # If operation targets a hospital resource, verify tenant matching
        if target_hospital_id:
            if not actor_hospital_id:
                # Denial: Actor has no hospital association
                cls._log_isolation_denial(
                    db, actor_role_norm, actor_id, actor_hospital_id, target_hospital_id,
                    resource_type, resource_id, "Actor lacks hospital affiliation"
                )
                return {
                    "allowed": False,
                    "reason": f"Access denied: Role '{actor_role_norm}' has no hospital association to access Hospital '{target_hospital_id}'.",
                    "actor_role": actor_role_norm,
                    "actor_hospital_id": actor_hospital_id,
                    "target_hospital_id": target_hospital_id
                }

            if actor_hospital_id != target_hospital_id:
                # Critical Cross-Tenant Violation Blocked!
                cls._log_isolation_denial(
                    db, actor_role_norm, actor_id, actor_hospital_id, target_hospital_id,
                    resource_type, resource_id, "Cross-tenant isolation boundary violation"
                )
                return {
                    "allowed": False,
                    "reason": f"Cross-tenant isolation violation: Hospital A ({actor_hospital_id}) user cannot access Hospital B ({target_hospital_id}) private data.",
                    "actor_role": actor_role_norm,
                    "actor_hospital_id": actor_hospital_id,
                    "target_hospital_id": target_hospital_id
                }

        # If resource is an Appointment, verify hospital ownership
        if resource_type.upper() == "APPOINTMENT" and resource_id:
            appt = db.query(Appointment).filter(Appointment.id == resource_id).first()
            if appt and appt.hospital_id != actor_hospital_id and actor_role_norm != "PLATFORM_ADMIN":
                cls._log_isolation_denial(
                    db, actor_role_norm, actor_id, actor_hospital_id, appt.hospital_id,
                    resource_type, resource_id, "Appointment belongs to a different hospital tenant"
                )
                return {
                    "allowed": False,
                    "reason": f"Cross-tenant violation: Appointment '{resource_id}' belongs to Hospital '{appt.hospital_id}', not '{actor_hospital_id}'.",
                    "actor_role": actor_role_norm
                }

        return {
            "allowed": True,
            "reason": "Tenant isolation check passed. Resource belongs to authorized hospital boundary.",
            "actor_role": actor_role_norm,
            "hospital_id": actor_hospital_id
        }

    @classmethod
    def _log_isolation_denial(
        cls,
        db: Session,
        actor_role: str,
        actor_id: str,
        actor_hospital_id: Optional[str],
        target_hospital_id: Optional[str],
        resource_type: str,
        resource_id: Optional[str],
        reason: str
    ):
        audit = PrivacyAccessAudit(
            requester_role=actor_role,
            requester_id=actor_id,
            hospital_id=actor_hospital_id or target_hospital_id,
            resource_type=f"TENANT_DATA_{resource_type.upper()}",
            resource_id=resource_id,
            action="ACCESS_DENIED",
            decision="DENIED",
            reason=f"Security Violation: {reason}. Actor: {actor_id} (Hosp: {actor_hospital_id}) -> Target: {target_hospital_id}"
        )
        db.add(audit)
        try:
            db.commit()
        except Exception:
            db.rollback()


tenant_isolation_enforcer = TenantIsolationEnforcer()
