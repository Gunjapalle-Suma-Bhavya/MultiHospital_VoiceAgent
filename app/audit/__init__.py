"""
Audit Trail & Privacy-Aware Logging Package (Sections 5.40 & 5.41).

Defines:
- 7 Audit Objectives (Section 5.40)
- Canonical Lifecycle Event Types (Section 5.40)
- 6 Permission-Controlled Healthcare Resources (Section 5.41)
- Role Permission Matrix for Privacy Governance
"""

from enum import Enum
from typing import Dict, List, Set


class AuditCategory(str, Enum):
    """The 7 core audit objectives from Section 5.40."""
    DEBUGGING = "DEBUGGING"
    RELIABILITY = "RELIABILITY"
    OPERATIONAL_MONITORING = "OPERATIONAL_MONITORING"
    DISPUTE_INVESTIGATION = "DISPUTE_INVESTIGATION"
    AGENT_EVALUATION = "AGENT_EVALUATION"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    INTEGRATION_TROUBLESHOOTING = "INTEGRATION_TROUBLESHOOTING"


class ProtectedResource(str, Enum):
    """The 6 sensitive resources subject to permission-controlled access in Section 5.41."""
    PATIENT_INFO = "PATIENT_INFO"
    TRANSCRIPTS = "TRANSCRIPTS"
    QUESTIONNAIRE_RESPONSES = "QUESTIONNAIRE_RESPONSES"
    RECORDINGS = "RECORDINGS"
    OPERATIONAL_DETAILS = "OPERATIONAL_DETAILS"
    INTEGRATION_DETAILS = "INTEGRATION_DETAILS"


class AuditEventType(str, Enum):
    """Canonical lifecycle events and structured operational occurrences."""
    CALL_STARTED = "CALL_STARTED"
    PATIENT_IDENTIFIED = "PATIENT_IDENTIFIED"
    AI_CONTEXT_RETRIEVED = "AI_CONTEXT_RETRIEVED"
    TOOL_CALL = "TOOL_CALL"
    PATIENT_SELECTED_SLOT = "PATIENT_SELECTED_SLOT"
    BOOKING_STARTED = "BOOKING_STARTED"
    EHR_INTEGRATION_STARTED = "EHR_INTEGRATION_STARTED"
    EXTERNAL_APPOINTMENT_CREATED = "EXTERNAL_APPOINTMENT_CREATED"
    EHR_SYNC_VERIFIED = "EHR_SYNC_VERIFIED"
    BOOKING_VERIFIED = "BOOKING_VERIFIED"
    QUESTIONNAIRE_STARTED = "QUESTIONNAIRE_STARTED"
    QUESTIONNAIRE_COMPLETED = "QUESTIONNAIRE_COMPLETED"
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    CALL_COMPLETED = "CALL_COMPLETED"
    
    # Operational search & booking
    APPOINTMENT_SEARCHED = "APPOINTMENT_SEARCHED"
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_RESCHEDULED = "APPOINTMENT_RESCHEDULED"
    
    # Escalation & Security
    HUMAN_ESCALATION_TRIGGERED = "HUMAN_ESCALATION_TRIGGERED"
    SECURITY_ACCESS_CHECK = "SECURITY_ACCESS_CHECK"
    PRIVACY_VIOLATION_BLOCKED = "PRIVACY_VIOLATION_BLOCKED"


class PrivacyLevel(str, Enum):
    STRUCTURED_NO_PHI = "STRUCTURED_NO_PHI"
    REDACTED_PHI = "REDACTED_PHI"
    ANONYMIZED = "ANONYMIZED"


class AccessDecision(str, Enum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"


# Default mapping from event type to primary audit category
EVENT_CATEGORY_MAP: Dict[str, AuditCategory] = {
    AuditEventType.CALL_STARTED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.PATIENT_IDENTIFIED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.AI_CONTEXT_RETRIEVED.value: AuditCategory.AGENT_EVALUATION,
    AuditEventType.TOOL_CALL.value: AuditCategory.DEBUGGING,
    AuditEventType.PATIENT_SELECTED_SLOT.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.BOOKING_STARTED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.EHR_INTEGRATION_STARTED.value: AuditCategory.INTEGRATION_TROUBLESHOOTING,
    AuditEventType.EXTERNAL_APPOINTMENT_CREATED.value: AuditCategory.INTEGRATION_TROUBLESHOOTING,
    AuditEventType.EHR_SYNC_VERIFIED.value: AuditCategory.RELIABILITY,
    AuditEventType.BOOKING_VERIFIED.value: AuditCategory.RELIABILITY,
    AuditEventType.QUESTIONNAIRE_STARTED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.QUESTIONNAIRE_COMPLETED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.WORKFLOW_STARTED.value: AuditCategory.RELIABILITY,
    AuditEventType.CALL_COMPLETED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.APPOINTMENT_SEARCHED.value: AuditCategory.OPERATIONAL_MONITORING,
    AuditEventType.APPOINTMENT_BOOKED.value: AuditCategory.DISPUTE_INVESTIGATION,
    AuditEventType.HUMAN_ESCALATION_TRIGGERED.value: AuditCategory.DISPUTE_INVESTIGATION,
    AuditEventType.SECURITY_ACCESS_CHECK.value: AuditCategory.SECURITY_REVIEW,
    AuditEventType.PRIVACY_VIOLATION_BLOCKED.value: AuditCategory.SECURITY_REVIEW,
}

# Role permission matrix for the 6 protected healthcare resource categories (Section 5.41)
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "PLATFORM_ADMIN": {
        ProtectedResource.OPERATIONAL_DETAILS.value,
        ProtectedResource.INTEGRATION_DETAILS.value,
    },
    "HOSPITAL_ADMIN": {
        ProtectedResource.OPERATIONAL_DETAILS.value,
        ProtectedResource.INTEGRATION_DETAILS.value,
        ProtectedResource.QUESTIONNAIRE_RESPONSES.value,
        ProtectedResource.PATIENT_INFO.value,
    },
    "DOCTOR": {
        ProtectedResource.PATIENT_INFO.value,
        ProtectedResource.QUESTIONNAIRE_RESPONSES.value,
        ProtectedResource.OPERATIONAL_DETAILS.value,
    },
    "PATIENT": {
        ProtectedResource.PATIENT_INFO.value,
        ProtectedResource.QUESTIONNAIRE_RESPONSES.value,
    },
    "CALL_OPERATOR": {
        ProtectedResource.PATIENT_INFO.value,
        ProtectedResource.TRANSCRIPTS.value,
    },
    "AUDITOR": {
        ProtectedResource.OPERATIONAL_DETAILS.value,
        ProtectedResource.INTEGRATION_DETAILS.value,
    },
}
