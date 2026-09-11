"""
Context Security & Privacy Guard (Section 17.1).

Enforces:
1. Persistent user context follows the same authorization boundaries as primary user data.
2. Prevention of:
   - Cross-user context leakage (Patient A cannot see Patient B's history or answers)
   - Cross-hospital context leakage (Doctor in Hospital A cannot receive context from Hospital B)
   - Unauthorized context retrieval
   - Context exposure through AI responses (leaking internal IDs, DB keys, other patient info)
3. Minimum Necessary Rule:
   - The AI retrieves ONLY the context required for the current operation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models import PatientProfile, Appointment, PrivacyAccessAudit


class ContextRetrievalFilter(BaseModel):
    caller_role: str
    caller_patient_id: Optional[str] = None
    caller_hospital_id: Optional[str] = None
    target_patient_id: str
    target_hospital_id: Optional[str] = None
    operation_type: str = "SCHEDULE_APPOINTMENT"  # Minimal context filter scope


class ContextSecurityGuard:
    """
    Guards context retrieval and AI prompt synthesis from data leakage.
    """

    @classmethod
    def filter_context_for_operation(
        cls,
        db: Session,
        filter_req: ContextRetrievalFilter,
        raw_context_bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enforces Section 17.1 Context Security:
        1. Checks cross-user boundary.
        2. Checks cross-hospital boundary.
        3. Applies Minimal Necessary filter based on operation_type.
        4. Scrubs internal database identifiers (e.g. internal UUIDs, DB table keys).
        """
        role = (filter_req.caller_role or "PATIENT").upper()

        # 1. Cross-User Check: If caller is a Patient, caller_patient_id MUST match target_patient_id
        if role == "PATIENT":
            if filter_req.caller_patient_id and filter_req.caller_patient_id != filter_req.target_patient_id:
                cls._log_context_leakage_attempt(
                    db, role, filter_req.caller_patient_id, filter_req.target_patient_id,
                    "CROSS_USER_CONTEXT_LEAKAGE_PREVENTED"
                )
                return {
                    "authorized": False,
                    "error": "CROSS_USER_LEAKAGE_PREVENTED",
                    "message": "Patient cannot retrieve context belonging to another patient.",
                    "sanitized_context": {}
                }

        # 2. Cross-Hospital Check: If caller is Hospital Admin/Doctor, hospital must match
        if role in ["HOSPITAL_ADMIN", "DOCTOR"]:
            if filter_req.caller_hospital_id and filter_req.target_hospital_id:
                if filter_req.caller_hospital_id != filter_req.target_hospital_id:
                    cls._log_context_leakage_attempt(
                        db, role, filter_req.caller_hospital_id, filter_req.target_hospital_id,
                        "CROSS_HOSPITAL_CONTEXT_LEAKAGE_PREVENTED"
                    )
                    return {
                        "authorized": False,
                        "error": "CROSS_HOSPITAL_LEAKAGE_PREVENTED",
                        "message": "Hospital/Doctor cannot retrieve context belonging to another hospital.",
                        "sanitized_context": {}
                    }

        # 3. Minimal Necessary Context Rule
        # AI retrieves only what is required for current operation_type
        sanitized = {}
        tier1 = raw_context_bundle.get("tier1_conversation_state", {})
        tier3 = raw_context_bundle.get("tier3_long_term", {})
        tier4 = raw_context_bundle.get("tier4_appointment_info", {})

        if filter_req.operation_type in ["SCHEDULE_APPOINTMENT", "DISCOVER_DOCTOR"]:
            # Needs only: specialty, date, preferred doctor/time window
            sanitized["conversation_state"] = {
                "intent": tier1.get("intent"),
                "specialty": tier1.get("specialty"),
                "preferred_time": tier1.get("time_preference")
            }
            sanitized["preferences"] = {
                "preferred_time_window": tier3.get("preferred_time_window"),
                "communication_preference": tier3.get("communication_preference")
            }
            # Exclude full medical history or cross-visit questionnaire answers
            sanitized["minimal_scope_applied"] = True

        elif filter_req.operation_type == "CHECK_UPCOMING_APPOINTMENT":
            sanitized["upcoming_appointments"] = tier4.get("upcoming_appointments", [])
            sanitized["minimal_scope_applied"] = True

        else:
            # General minimal profile
            sanitized["conversation_state"] = tier1
            sanitized["minimal_scope_applied"] = False

        # 4. Prevent Context Exposure Through AI Responses (scrub internal IDs)
        cleaned_json = cls._scrub_internal_identifiers(sanitized)

        return {
            "authorized": True,
            "leakage_checks_passed": True,
            "operation_type": filter_req.operation_type,
            "sanitized_context": cleaned_json
        }

    @classmethod
    def _scrub_internal_identifiers(cls, data: Any) -> Any:
        """Removes internal DB primary keys, schema tokens, and confidential fields."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if k in ["db_id", "internal_id", "sql_session_key", "password_hash", "access_token"]:
                    continue
                new_dict[k] = cls._scrub_internal_identifiers(v)
            return new_dict
        elif isinstance(data, list):
            return [cls._scrub_internal_identifiers(i) for i in data]
        return data

    @classmethod
    def _log_context_leakage_attempt(
        cls, db: Session, role: str, actor_id: Optional[str], target_id: str, violation_code: str
    ):
        audit = PrivacyAccessAudit(
            requester_role=role,
            requester_id=actor_id or "ANONYMOUS",
            resource_type="USER_CONTEXT",
            resource_id=target_id,
            action="CONTEXT_RETRIEVAL_BLOCKED",
            decision="DENIED",
            reason=f"Context Security Alert: {violation_code}. Requester: {actor_id} tried accessing context of {target_id}."
        )
        db.add(audit)
        try:
            db.commit()
        except Exception:
            db.rollback()


context_security_guard = ContextSecurityGuard()
