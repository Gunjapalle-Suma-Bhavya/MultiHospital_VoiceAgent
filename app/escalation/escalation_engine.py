"""
Escalation Engine (Section 5.39).

Manages the full human escalation lifecycle:
1. trigger_escalation()    — Record the escalation with typed trigger reason + context snapshot
2. get_escalation_context()— Return the authorized context package for the operator
3. resolve_escalation()    — Mark RESOLVED or TRANSFERRED_BACK_TO_AI
4. list_escalation_records()— Filter/list for dashboard display
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.database.models import HumanEscalationRecord
from app.escalation import ESCALATION_TRIGGER_REASONS, RESOLUTION_STATUSES


class EscalationEngine:
    """
    Central engine for human escalation operations.
    Ensures every AI-to-human handoff is recorded, contextualized, and resolvable.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    # -------------------------------------------------------------------------
    # 1. Trigger Escalation
    # -------------------------------------------------------------------------
    def trigger_escalation(
        self,
        session_id: str,
        trigger_reason: str,
        hospital_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        failure_count: int = 0,
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record a new human escalation.

        Args:
            session_id:       The AI conversation session ID.
            trigger_reason:   One of the 8 typed trigger reasons.
            hospital_id:      Hospital scope (optional).
            trace_id:         Links to an OperationTrace record (optional).
            failure_count:    Number of retries / failures before escalation.
            context_snapshot: Dict with patient-facing context for operator handoff.
                              Should contain: intent, actions_attempted, patient_info,
                              last_error, conversation_summary.

        Returns:
            Dict with escalation_id, resolution_status, escalated_at, and full record.
        """
        if trigger_reason not in ESCALATION_TRIGGER_REASONS:
            raise ValueError(
                f"Invalid trigger_reason '{trigger_reason}'. "
                f"Must be one of: {ESCALATION_TRIGGER_REASONS}"
            )

        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"

        # Package the authorized context — include defaults for missing keys
        if context_snapshot is None:
            context_snapshot = {}

        handoff_context = {
            "escalation_id": escalation_id,
            "session_id": session_id,
            "hospital_id": hospital_id,
            "trigger_reason": trigger_reason,
            "failure_count": failure_count,
            "trace_id": trace_id,
            "patient_intent": context_snapshot.get("patient_intent", "Unknown"),
            "conversation_summary": context_snapshot.get("conversation_summary", ""),
            "actions_attempted": context_snapshot.get("actions_attempted", []),
            "last_error": context_snapshot.get("last_error", None),
            "patient_info": context_snapshot.get("patient_info", {}),
            "escalated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "operator_guidance": self._build_operator_guidance(trigger_reason),
        }

        record = HumanEscalationRecord(
            escalation_id=escalation_id,
            session_id=session_id,
            hospital_id=hospital_id,
            trace_id=trace_id,
            trigger_reason=trigger_reason,
            failure_count=failure_count,
            authorized_context_json=json.dumps(handoff_context),
            resolution_status="ESCALATED",
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return {
            "escalation_id": escalation_id,
            "resolution_status": record.resolution_status,
            "trigger_reason": trigger_reason,
            "failure_count": failure_count,
            "hospital_id": hospital_id,
            "session_id": session_id,
            "trace_id": trace_id,
            "escalated_at": record.escalated_at.isoformat() if record.escalated_at else None,
            "message": f"Escalation triggered. Ticket: {escalation_id}. Human operator required.",
        }

    # -------------------------------------------------------------------------
    # 2. Get Escalation Context (for operator handoff)
    # -------------------------------------------------------------------------
    def get_escalation_context(self, escalation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the authorized context package for a human operator.

        Returns:
            The full context dict that the operator should see, or None if not found.
        """
        record = self.db.query(HumanEscalationRecord).filter(
            HumanEscalationRecord.escalation_id == escalation_id
        ).first()

        if not record:
            return None

        context = {}
        if record.authorized_context_json:
            try:
                context = json.loads(record.authorized_context_json)
            except (json.JSONDecodeError, TypeError):
                context = {"raw": record.authorized_context_json}

        return {
            "escalation_id": record.escalation_id,
            "session_id": record.session_id,
            "hospital_id": record.hospital_id,
            "trigger_reason": record.trigger_reason,
            "failure_count": record.failure_count,
            "resolution_status": record.resolution_status,
            "escalated_at": record.escalated_at.isoformat() if record.escalated_at else None,
            "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
            "operator_id": record.operator_id,
            "operator_notes": record.operator_notes,
            "authorized_context": context,
        }

    # -------------------------------------------------------------------------
    # 3. Resolve Escalation
    # -------------------------------------------------------------------------
    def resolve_escalation(
        self,
        escalation_id: str,
        resolution_status: str,
        operator_id: Optional[str] = None,
        operator_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mark an escalation as RESOLVED or TRANSFERRED_BACK_TO_AI.

        Args:
            escalation_id:     The escalation ticket ID.
            resolution_status: RESOLVED or TRANSFERRED_BACK_TO_AI.
            operator_id:       ID/name of the human operator.
            operator_notes:    Free-form notes from the operator.

        Returns:
            Updated record dict or None if not found.
        """
        valid_resolutions = ["RESOLVED", "TRANSFERRED_BACK_TO_AI"]
        if resolution_status not in valid_resolutions:
            raise ValueError(
                f"Invalid resolution_status '{resolution_status}'. "
                f"Must be one of: {valid_resolutions}"
            )

        record = self.db.query(HumanEscalationRecord).filter(
            HumanEscalationRecord.escalation_id == escalation_id
        ).first()

        if not record:
            return None

        record.resolution_status = resolution_status
        record.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if operator_id:
            record.operator_id = operator_id
        if operator_notes:
            record.operator_notes = operator_notes

        self.db.commit()
        self.db.refresh(record)

        return {
            "escalation_id": record.escalation_id,
            "resolution_status": record.resolution_status,
            "operator_id": record.operator_id,
            "operator_notes": record.operator_notes,
            "escalated_at": record.escalated_at.isoformat() if record.escalated_at else None,
            "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
            "message": f"Escalation {escalation_id} marked as {resolution_status}.",
        }

    # -------------------------------------------------------------------------
    # 4. List Escalation Records
    # -------------------------------------------------------------------------
    def list_escalation_records(
        self,
        hospital_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Filtered list of escalation records for dashboard display.
        """
        query = self.db.query(HumanEscalationRecord)
        if hospital_id:
            query = query.filter(HumanEscalationRecord.hospital_id == hospital_id)
        if status:
            query = query.filter(HumanEscalationRecord.resolution_status == status)

        records = query.order_by(HumanEscalationRecord.escalated_at.desc()).limit(limit).all()

        return [
            {
                "escalation_id": r.escalation_id,
                "session_id": r.session_id,
                "hospital_id": r.hospital_id,
                "trigger_reason": r.trigger_reason,
                "failure_count": r.failure_count,
                "resolution_status": r.resolution_status,
                "operator_id": r.operator_id,
                "escalated_at": r.escalated_at.isoformat() if r.escalated_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in records
        ]

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _build_operator_guidance(self, trigger_reason: str) -> str:
        """
        Build a short human-readable guidance string for the operator based on the trigger.
        """
        guidance_map = {
            "PATIENT_REQUESTED": "The patient explicitly asked to speak with a human. Greet them and confirm you have their details.",
            "BOOKING_SYSTEM_FAILURE": "The booking system could not complete the appointment after multiple retries. Assist with manual booking.",
            "EHR_INTEGRATION_FAILURE": "The EHR system could not be reached or verify data. Proceed with manual EHR record update.",
            "VERIFICATION_FAILURE": "External state could not be verified. Review the appointment or record and manually confirm.",
            "IDENTITY_UNRESOLVABLE": "The patient's identity could not be confirmed. Verify identity manually before proceeding.",
            "MISSING_REQUIRED_INFO": "Required information was not available. Ask the patient for the missing details.",
            "UNSUPPORTED_REQUEST": "The patient made a request the AI could not handle. Assess and resolve directly.",
            "SAFETY_POLICY": "A safety-related trigger was detected. Handle with care and follow escalation protocol.",
        }
        return guidance_map.get(trigger_reason, "Review the context and assist the patient.")
