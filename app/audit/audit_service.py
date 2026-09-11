"""
Audit Service (Sections 5.40 & 5.41).

Central engine for enterprise-grade auditable event logging, timeline reconstruction,
and privacy-aware operational monitoring.

Supports:
- 7 Audit Objectives: DEBUGGING, RELIABILITY, OPERATIONAL_MONITORING, DISPUTE_INVESTIGATION,
  AGENT_EVALUATION, SECURITY_REVIEW, INTEGRATION_TROUBLESHOOTING.
- Automatic privacy sanitization (zero raw PHI/transcripts in operational logs).
- Chronological timeline reconstruction (e.g., 15:42:01 CALL_STARTED).
- Multi-parameter filtering and statistical aggregations.
- Trail integrity verification.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import AuditLog
from app.audit import (
    AuditCategory, AuditEventType, EVENT_CATEGORY_MAP, PrivacyLevel
)
from app.audit.privacy_sanitizer import PrivacySanitizer


class AuditService:
    """
    Unified Audit Trail & Compliance Service.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    # -------------------------------------------------------------------------
    # 1. Record Auditable Event (Section 5.40 + 5.41)
    # -------------------------------------------------------------------------
    def record_event(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        hospital_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        category: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: str = "SYSTEM",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        timestamp: Optional[datetime] = None,
    ) -> AuditLog:
        """
        Records an auditable event, applying automatic PHI redaction and category assignment.
        """
        # Determine category from map if not explicitly passed
        if not category:
            matched_cat = EVENT_CATEGORY_MAP.get(event_type)
            category = matched_cat.value if matched_cat else AuditCategory.OPERATIONAL_MONITORING.value

        # Privacy sanitization of payload
        sanitized_payload, privacy_level = PrivacySanitizer.sanitize_payload(payload)

        # Sanitization of tool invocation if present
        tool_invocation_json = None
        if tool_name:
            tool_data = PrivacySanitizer.sanitize_tool_invocation(tool_name, tool_arguments)
            tool_invocation_json = json.dumps(tool_data, default=str)

        log_entry = AuditLog(
            session_id=session_id,
            hospital_id=hospital_id,
            correlation_id=correlation_id,
            event_type=event_type,
            category=category,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            privacy_level=privacy_level,
            tool_invocation_json=tool_invocation_json,
            payload_json=json.dumps(sanitized_payload, default=str) if sanitized_payload else None,
            timestamp=timestamp or datetime.now(timezone.utc).replace(tzinfo=None),
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    # -------------------------------------------------------------------------
    # 2. Chronological Timeline Reconstruction (Section 5.40 Specification)
    # -------------------------------------------------------------------------
    def get_session_timeline(self, session_id: str) -> Dict[str, Any]:
        """
        Reconstructs the chronological timeline of events for a call/session,
        matching the specification format (e.g. 15:42:01 CALL_STARTED, 15:42:11 TOOL_CALL: lookup_patient).
        """
        records = (
            self.db.query(AuditLog)
            .filter(AuditLog.session_id == session_id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )

        timeline_entries = []
        formatted_lines = []

        for r in records:
            time_str = r.timestamp.strftime("%H:%M:%S") if r.timestamp else "00:00:00"
            display_name = r.event_type

            # Format tool calls specifically as TOOL_CALL: <name>
            if r.tool_invocation_json:
                try:
                    tool_meta = json.loads(r.tool_invocation_json)
                    t_name = tool_meta.get("tool_name")
                    if t_name:
                        display_name = f"TOOL_CALL: {t_name}"
                except Exception:
                    pass

            line = f"{time_str} {display_name}"
            formatted_lines.append(line)

            payload = json.loads(r.payload_json) if r.payload_json else {}
            tool_invocation = json.loads(r.tool_invocation_json) if r.tool_invocation_json else None

            timeline_entries.append({
                "id": r.id,
                "time": time_str,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "display_line": line,
                "event_type": r.event_type,
                "category": r.category,
                "actor_role": r.actor_role,
                "actor_id": r.actor_id,
                "status": r.status,
                "privacy_level": r.privacy_level,
                "tool_invocation": tool_invocation,
                "payload": payload,
            })

        return {
            "session_id": session_id,
            "event_count": len(timeline_entries),
            "formatted_summary": "\n".join(formatted_lines),
            "timeline": timeline_entries,
        }

    # -------------------------------------------------------------------------
    # 3. Query Audit Logs (Filter by 7 Categories, Event Types, Hospital, Range)
    # -------------------------------------------------------------------------
    def query_audit_logs(
        self,
        category: Optional[str] = None,
        event_type: Optional[str] = None,
        hospital_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Queries structured audit records with support for all 7 audit objectives."""
        query = self.db.query(AuditLog)

        if category:
            query = query.filter(AuditLog.category == category.upper())
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if hospital_id:
            query = query.filter(AuditLog.hospital_id == hospital_id)
        if session_id:
            query = query.filter(AuditLog.session_id == session_id)
        if correlation_id:
            query = query.filter(AuditLog.correlation_id == correlation_id)
        if actor_role:
            query = query.filter(AuditLog.actor_role == actor_role.upper())
        if status:
            query = query.filter(AuditLog.status == status.upper())

        records = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

        results = []
        for r in records:
            results.append({
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "session_id": r.session_id,
                "hospital_id": r.hospital_id,
                "correlation_id": r.correlation_id,
                "event_type": r.event_type,
                "category": r.category,
                "actor_role": r.actor_role,
                "actor_id": r.actor_id,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "status": r.status,
                "privacy_level": r.privacy_level,
                "tool_invocation": json.loads(r.tool_invocation_json) if r.tool_invocation_json else None,
                "payload": json.loads(r.payload_json) if r.payload_json else {},
            })
        return results

    # -------------------------------------------------------------------------
    # 4. Audit Summary & Compliance Metrics
    # -------------------------------------------------------------------------
    def get_audit_summary(self, hospital_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates audit trail statistics and privacy compliance distribution."""
        query = self.db.query(AuditLog)
        if hospital_id:
            query = query.filter(AuditLog.hospital_id == hospital_id)

        total_events = query.count()

        # Group by Category (the 7 audit objectives)
        category_counts = {}
        for cat in AuditCategory:
            count = query.filter(AuditLog.category == cat.value).count()
            category_counts[cat.value] = count

        # Group by Privacy Level (Section 5.41 compliance)
        privacy_distribution = {}
        for pl in PrivacyLevel:
            count = query.filter(AuditLog.privacy_level == pl.value).count()
            privacy_distribution[pl.value] = count

        # Group by Status
        success_count = query.filter(AuditLog.status == "SUCCESS").count()
        failure_count = query.filter(AuditLog.status == "FAILURE").count()

        return {
            "hospital_id": hospital_id,
            "total_audit_events": total_events,
            "categories": category_counts,
            "privacy_compliance": privacy_distribution,
            "status_summary": {
                "SUCCESS": success_count,
                "FAILURE": failure_count,
                "OTHER": max(0, total_events - success_count - failure_count),
            },
        }

    # -------------------------------------------------------------------------
    # 5. Integrity Verification
    # -------------------------------------------------------------------------
    def verify_trail_integrity(self, session_id: str) -> Dict[str, Any]:
        """
        Validates the lifecycle checkpoints for a given session.
        Checks for chronological order and essential milestone events.
        """
        records = (
            self.db.query(AuditLog)
            .filter(AuditLog.session_id == session_id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )

        if not records:
            return {"session_id": session_id, "is_valid": False, "reason": "No audit records found"}

        event_types = [r.event_type for r in records]
        timestamps = [r.timestamp for r in records if r.timestamp]

        # 1. Chronological order check
        is_chronological = all(t1 <= t2 for t1, t2 in zip(timestamps, timestamps[1:]))

        # 2. Key lifecycle milestones presence check
        has_start = AuditEventType.CALL_STARTED.value in event_types or "AI_CONVERSATION_STARTED" in event_types
        has_patient = AuditEventType.PATIENT_IDENTIFIED.value in event_types
        has_complete = AuditEventType.CALL_COMPLETED.value in event_types

        integrity_issues = []
        if not is_chronological:
            integrity_issues.append("Timestamps are not strictly chronological")
        if not has_start:
            integrity_issues.append("Missing call/conversation start event")

        return {
            "session_id": session_id,
            "is_valid": len(integrity_issues) == 0,
            "is_chronological": is_chronological,
            "has_call_start": has_start,
            "has_patient_identified": has_patient,
            "has_call_complete": has_complete,
            "total_recorded_steps": len(records),
            "integrity_issues": integrity_issues,
        }
