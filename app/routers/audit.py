"""
Audit Trail & Privacy-Aware Logging Router (Sections 5.40 & 5.41).

Exposes REST APIs for:
- Auditable event recording (with auto-sanitization)
- Chronological timeline inspection
- Querying across the 7 audit objectives
- Privacy access evaluation & security audit logs
- Role permission matrix inspection
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.audit import (
    AuditCategory, AuditEventType, ProtectedResource,
    ROLE_PERMISSIONS, PrivacyLevel
)
from app.audit.audit_service import AuditService
from app.audit.privacy_access_controller import PrivacyAccessController

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Trail & Privacy Logging"])


# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------
class RecordEventRequest(BaseModel):
    event_type: str = Field(..., description="Canonical event type, e.g. CALL_STARTED, APPOINTMENT_BOOKED")
    session_id: Optional[str] = None
    hospital_id: Optional[str] = None
    correlation_id: Optional[str] = None
    category: Optional[str] = Field(None, description="One of the 7 audit objectives")
    actor_id: Optional[str] = None
    actor_role: str = "SYSTEM"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    status: str = "SUCCESS"


class PrivacyAccessCheckRequest(BaseModel):
    requester_role: str = Field(..., description="Role requesting access (e.g. DOCTOR, PATIENT, HOSPITAL_ADMIN)")
    requester_id: str = Field(..., description="ID of requester")
    resource_type: str = Field(..., description="One of the 6 protected resources, e.g. PATIENT_INFO, RECORDINGS")
    resource_id: Optional[str] = None
    hospital_id: Optional[str] = None
    user_hospital_id: Optional[str] = None
    action: str = "READ"
    reason: Optional[str] = None


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.post("/events", status_code=status.HTTP_201_CREATED)
def record_audit_event(req: RecordEventRequest, db: Session = Depends(get_db)):
    """
    Records an auditable event with automatic PHI sanitization and category assignment.
    """
    svc = AuditService(db)
    log_entry = svc.record_event(
        event_type=req.event_type,
        session_id=req.session_id,
        hospital_id=req.hospital_id,
        correlation_id=req.correlation_id,
        category=req.category,
        actor_id=req.actor_id,
        actor_role=req.actor_role,
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        tool_name=req.tool_name,
        tool_arguments=req.tool_arguments,
        payload=req.payload,
        status=req.status,
    )
    return {
        "status": "success",
        "audit_id": log_entry.id,
        "event_type": log_entry.event_type,
        "category": log_entry.category,
        "privacy_level": log_entry.privacy_level,
        "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
    }


@router.get("/trail")
def query_audit_trail(
    category: Optional[str] = Query(None, description="One of the 7 audit objectives"),
    event_type: Optional[str] = Query(None, description="Specific event type"),
    hospital_id: Optional[str] = None,
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Queries audit records supporting the 7 audit objectives:
    DEBUGGING, RELIABILITY, OPERATIONAL_MONITORING, DISPUTE_INVESTIGATION,
    AGENT_EVALUATION, SECURITY_REVIEW, INTEGRATION_TROUBLESHOOTING.
    """
    svc = AuditService(db)
    events = svc.query_audit_logs(
        category=category,
        event_type=event_type,
        hospital_id=hospital_id,
        session_id=session_id,
        correlation_id=correlation_id,
        actor_role=actor_role,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "count": len(events),
        "limit": limit,
        "offset": offset,
        "events": events,
    }


@router.get("/timeline/{session_id}")
def get_session_timeline(session_id: str, db: Session = Depends(get_db)):
    """
    Reconstructs the chronological event timeline for a call/session (Section 5.40).
    """
    svc = AuditService(db)
    timeline_data = svc.get_session_timeline(session_id)
    integrity = svc.verify_trail_integrity(session_id)
    timeline_data["integrity"] = integrity
    return timeline_data


@router.get("/summary")
def get_audit_summary(hospital_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Aggregates statistics by the 7 audit objectives and Section 5.41 privacy levels.
    """
    svc = AuditService(db)
    return svc.get_audit_summary(hospital_id=hospital_id)


@router.post("/privacy/access-check")
def check_privacy_access(req: PrivacyAccessCheckRequest, db: Session = Depends(get_db)):
    """
    Evaluates permission-controlled access to the 6 sensitive healthcare resources (Section 5.41).
    Logs the access attempt into PrivacyAccessAudit and general audit trail if denied.
    """
    result = PrivacyAccessController.evaluate_access(
        db=db,
        requester_role=req.requester_role,
        requester_id=req.requester_id,
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        hospital_id=req.hospital_id,
        user_hospital_id=req.user_hospital_id,
        action=req.action,
        reason=req.reason,
    )
    if not result["authorized"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result,
        )
    return result


@router.get("/privacy/access-logs")
def list_privacy_access_logs(
    hospital_id: Optional[str] = None,
    requester_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Queries historical access check attempts and security audit logs for sensitive resources.
    """
    logs = PrivacyAccessController.list_access_audits(
        db=db,
        hospital_id=hospital_id,
        requester_role=requester_role,
        resource_type=resource_type,
        decision=decision,
        limit=limit,
    )
    return {"count": len(logs), "access_logs": logs}


@router.get("/privacy/permissions")
def get_permissions_matrix():
    """
    Returns the role-based permission matrix for the 6 protected healthcare resource categories.
    """
    return {
        "protected_resources": [r.value for r in ProtectedResource],
        "role_permissions": {role: list(res) for role, res in ROLE_PERMISSIONS.items()},
    }


@router.get("/categories")
def get_audit_metadata():
    """
    Returns the 7 audit objectives and supported canonical event types.
    """
    return {
        "audit_objectives": [c.value for c in AuditCategory],
        "protected_resources": [r.value for r in ProtectedResource],
        "canonical_event_types": [e.value for e in AuditEventType],
        "privacy_levels": [p.value for p in PrivacyLevel],
    }
