"""
Observability & Correlation Engine (Sections 5.34 & 5.35).
Provides end-to-end operation lifecycle tracing, latency breakdown, failure diagnostics,
retry & recovery tracking, and cross-component correlation traceability.
"""

CANONICAL_LIFECYCLE_STEPS = [
    "CALL_STARTED",
    "PATIENT_IDENTIFIED",
    "INTENT_DETECTED",
    "CONTEXT_RETRIEVED",
    "SEARCH_DOCTORS",
    "CHECK_AVAILABILITY",
    "PATIENT_SELECTED_SLOT",
    "BOOKING_STARTED",
    "EHR_INTEGRATION_STARTED",
    "EXTERNAL_RECORD_CREATED",
    "EHR_SYNC_VERIFIED",
    "BOOKING_VERIFIED",
    "QUESTIONNAIRE_STARTED",
    "QUESTIONNAIRE_COMPLETED",
    "NOTIFICATION_SENT",
    "CALL_COMPLETED"
]

COMPONENT_TYPES = [
    "CONVERSATION",
    "AI_DECISION",
    "CAPABILITY_CALL",
    "SCHEDULING",
    "EHR_INTEGRATION",
    "VERIFICATION",
    "SYNCHRONIZATION",
    "WORKFLOW",
    "NOTIFICATION",
    "AUDIT_EVENT"
]

from app.observability.trace_manager import TraceManager
from app.observability.observability_service import ObservabilityService

__all__ = [
    "CANONICAL_LIFECYCLE_STEPS",
    "COMPONENT_TYPES",
    "TraceManager",
    "ObservabilityService"
]
