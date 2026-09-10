"""
Persistent Patient Context Manager.

Implements clear data boundaries between:
1. Current conversation state
2. Short-term interaction context
3. Longer-term user preferences
4. Appointment-specific information
5. Sensitive healthcare information
6. System-generated operational data
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class UserPreferencesContext(BaseModel):
    last_hospital_id: Optional[str] = None
    last_doctor_name: Optional[str] = None
    preferred_time_window: Optional[str] = None  # e.g., "AFTERNOON", "MORNING"
    communication_preference: Optional[str] = "VOICE_AND_SMS"


class ActiveSessionContext(BaseModel):
    session_id: str
    current_intent: Optional[str] = None
    completed_steps: list[str] = []
    draft_booking: Dict[str, Any] = {}


class PatientContextBundle(BaseModel):
    """
    Structured context bundle passed to the LLM agent during turn execution.
    Excludes sensitive health information unless explicitly required for intake.
    """
    patient_id: str
    phone_number: str
    preferences: UserPreferencesContext
    session: ActiveSessionContext

    def generate_context_prompt_hint(self) -> str:
        """
        Generates non-intrusive system hints for natural voice interaction based on past history.
        Example: "Patient previously booked afternoon slots with Dr. Sharma."
        """
        hints = []
        if self.preferences.last_doctor_name:
            hints.append(f"Previously saw {self.preferences.last_doctor_name}.")
        if self.preferences.preferred_time_window:
            hints.append(f"Prefers {self.preferences.preferred_time_window.lower()} appointments.")
        
        if hints:
            return "CONTEXT HINT: " + " ".join(hints)
        return ""


class ContextBoundaryGuard:
    """
    Ensures sensitive health data is isolated and not leaked into general preference logs or system telemetry.
    """

    @staticmethod
    def sanitize_for_telemetry(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strips sensitive healthcare information before writing to operational AuditLog.
        """
        sanitized = data.copy()
        sensitive_fields = ["symptoms", "intake_answers", "medical_history", "patient_reported_summary"]
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED_SENSITIVE_HEALTH_INFO]"
        return sanitized
