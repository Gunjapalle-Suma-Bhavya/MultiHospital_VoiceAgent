"""
Escalation Package (Section 5.39).

Provides:
- ESCALATION_TRIGGER_REASONS: 8 typed trigger classifications
- RESOLUTION_STATUSES: allowed lifecycle states
- EscalationEngine: trigger, context retrieval, and resolution logic
"""

ESCALATION_TRIGGER_REASONS = [
    "PATIENT_REQUESTED",          # Patient explicitly asks for a human
    "BOOKING_SYSTEM_FAILURE",     # Booking system repeatedly fails
    "EHR_INTEGRATION_FAILURE",    # EHR integration repeatedly fails
    "VERIFICATION_FAILURE",       # External state cannot be verified
    "IDENTITY_UNRESOLVABLE",      # Identity cannot be established
    "MISSING_REQUIRED_INFO",      # Required information cannot be resolved
    "UNSUPPORTED_REQUEST",        # Complex or unsupported request
    "SAFETY_POLICY",              # Safety policy mandates escalation
]

RESOLUTION_STATUSES = [
    "ESCALATED",               # Active - awaiting human operator
    "RESOLVED",                # Fully resolved by human operator
    "TRANSFERRED_BACK_TO_AI",  # Handed back to the AI agent
]

from app.escalation.escalation_engine import EscalationEngine

__all__ = [
    "ESCALATION_TRIGGER_REASONS",
    "RESOLUTION_STATUSES",
    "EscalationEngine",
]
