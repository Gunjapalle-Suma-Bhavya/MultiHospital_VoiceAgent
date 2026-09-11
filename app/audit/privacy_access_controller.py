"""
Privacy Access Controller (Section 5.41).

Enforces role-based, tenant-isolated access controls over the 6 sensitive healthcare resources:
1. PATIENT_INFO
2. TRANSCRIPTS
3. QUESTIONNAIRE_RESPONSES
4. RECORDINGS
5. OPERATIONAL_DETAILS
6. INTEGRATION_DETAILS

Every access attempt (granted or denied) produces an immutable security audit entry in PrivacyAccessAudit.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database.models import PrivacyAccessAudit, AuditLog
from app.audit import (
    ProtectedResource, ROLE_PERMISSIONS, AccessDecision,
    AuditCategory, AuditEventType, PrivacyLevel
)


class PrivacyAccessController:
    """
    Evaluates permissions and enforces strict healthcare privacy compliance across all resources.
    """

    @classmethod
    def evaluate_access(
        cls,
        db: Session,
        requester_role: str,
        requester_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        hospital_id: Optional[str] = None,
        user_hospital_id: Optional[str] = None,
        action: str = "READ",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates whether a requester role is authorized to access a sensitive resource,
        enforcing role permissions and multi-tenant isolation.
        Automatically records a PrivacyAccessAudit row.
        """
        role_upper = (requester_role or "ANONYMOUS").upper()
        res_upper = (resource_type or "").upper()

        # Validate resource type
        valid_resources = [r.value for r in ProtectedResource]
        if res_upper not in valid_resources:
            decision = AccessDecision.DENIED.value
            justification = f"Invalid protected resource type '{resource_type}'. Must be one of {valid_resources}."
        else:
            # Check Role Permissions Matrix
            allowed_resources = ROLE_PERMISSIONS.get(role_upper, set())
            if res_upper not in allowed_resources:
                decision = AccessDecision.DENIED.value
                justification = f"Role '{role_upper}' does not have permission to access resource '{res_upper}'."
            
            # Check Multi-Tenant Hospital Isolation
            elif hospital_id and user_hospital_id and role_upper not in {"PLATFORM_ADMIN", "AUDITOR"}:
                if hospital_id != user_hospital_id:
                    decision = AccessDecision.DENIED.value
                    justification = f"Cross-tenant violation: Requester hospital '{user_hospital_id}' does not match target hospital '{hospital_id}'."
                else:
                    decision = AccessDecision.GRANTED.value
                    justification = f"Access granted to role '{role_upper}' for '{res_upper}'."
            else:
                decision = AccessDecision.GRANTED.value
                justification = f"Access granted to role '{role_upper}' for '{res_upper}'."

        if reason:
            justification += f" Context reason: {reason}"

        # Persist audit record in privacy_access_audits table
        audit_record = PrivacyAccessAudit(
            requester_role=role_upper,
            requester_id=requester_id,
            hospital_id=hospital_id or user_hospital_id,
            resource_type=res_upper,
            resource_id=resource_id,
            action=action.upper(),
            decision=decision,
            reason=justification,
        )
        db.add(audit_record)

        # If denied or security review required, also log to general AuditLog under SECURITY_REVIEW category
        if decision == AccessDecision.DENIED.value:
            sec_event = AuditLog(
                hospital_id=hospital_id or user_hospital_id,
                event_type=AuditEventType.PRIVACY_VIOLATION_BLOCKED.value,
                category=AuditCategory.SECURITY_REVIEW.value,
                actor_id=requester_id,
                actor_role=role_upper,
                resource_type=res_upper,
                resource_id=resource_id,
                status="DENIED",
                privacy_level=PrivacyLevel.STRUCTURED_NO_PHI.value,
                payload_json=f'{{"reason": "{justification}", "action": "{action}"}}',
            )
            db.add(sec_event)

        db.commit()
        db.refresh(audit_record)

        return {
            "authorized": decision == AccessDecision.GRANTED.value,
            "decision": decision,
            "requester_role": role_upper,
            "requester_id": requester_id,
            "resource_type": res_upper,
            "resource_id": resource_id,
            "action": action.upper(),
            "reason": justification,
            "audit_id": audit_record.id,
            "timestamp": audit_record.timestamp.isoformat() if audit_record.timestamp else None,
        }

    @classmethod
    def list_access_audits(
        cls,
        db: Session,
        hospital_id: Optional[str] = None,
        requester_role: Optional[str] = None,
        resource_type: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Queries the privacy access audit log with filtering."""
        query = db.query(PrivacyAccessAudit)
        if hospital_id:
            query = query.filter(PrivacyAccessAudit.hospital_id == hospital_id)
        if requester_role:
            query = query.filter(PrivacyAccessAudit.requester_role == requester_role.upper())
        if resource_type:
            query = query.filter(PrivacyAccessAudit.resource_type == resource_type.upper())
        if decision:
            query = query.filter(PrivacyAccessAudit.decision == decision.upper())

        records = query.order_by(PrivacyAccessAudit.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "requester_role": r.requester_role,
                "requester_id": r.requester_id,
                "hospital_id": r.hospital_id,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "action": r.action,
                "decision": r.decision,
                "reason": r.reason,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]
