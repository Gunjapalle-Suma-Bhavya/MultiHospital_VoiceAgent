"""
Unit tests for non-clinical guardrails and persistent patient context boundaries.
"""

from app.agent.guardrails import NonClinicalGuardrail
from app.agent.context_manager import ContextBoundaryGuard, PatientContextBundle, UserPreferencesContext, ActiveSessionContext


def test_guardrails_pass_valid_appointment_query():
    is_safe, response, meta = NonClinicalGuardrail.inspect_utterance("I need to see a dermatologist for skin irritation.")
    assert is_safe is True
    assert meta["data_category"] == "PATIENT_REPORTED_INFORMATION"


def test_guardrails_block_clinical_diagnosis():
    is_safe, response, meta = NonClinicalGuardrail.inspect_utterance("Can you diagnose me and tell me what medication should I take?")
    assert is_safe is False
    assert meta["type"] == "CLINICAL_BOUNDARY_VIOLATION"
    assert "cannot provide medical diagnoses" in response


def test_context_hint_generation():
    bundle = PatientContextBundle(
        patient_id="p-123",
        phone_number="+1234567890",
        preferences=UserPreferencesContext(
            last_doctor_name="Dr. Sharma",
            preferred_time_window="AFTERNOON"
        ),
        session=ActiveSessionContext(session_id="s-456")
    )
    hint = bundle.generate_context_prompt_hint()
    assert "Dr. Sharma" in hint
    assert "afternoon" in hint


def test_sensitive_telemetry_redaction():
    raw_event = {
        "event_type": "INTAKE_SUBMITTED",
        "patient_id": "p-123",
        "symptoms": "Severe rash on left arm",
        "preferred_window": "MORNING"
    }
    sanitized = ContextBoundaryGuard.sanitize_for_telemetry(raw_event)
    assert sanitized["symptoms"] == "[REDACTED_SENSITIVE_HEALTH_INFO]"
    assert sanitized["preferred_window"] == "MORNING"
