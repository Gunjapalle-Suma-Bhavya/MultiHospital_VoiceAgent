"""
Context-Aware Reference Resolver (Section 1.3).

Resolves indirect conversational statements against active session state and long-term context:
- "Book that one." -> Resolves to selected slot in draft booking context.
- "Same doctor as last time." -> Resolves to last_doctor_id from PatientProfile.
- "Actually, make it Friday." -> Modifies date in current session state while retaining doctor/hospital.
- "Cancel my upcoming appointment." -> Resolves active appointment; asks clarification if multiple.
- "Reschedule that appointment to Monday." -> Resolves appointment and updates target day.

Rule: When context is ambiguous, requests clarification instead of guessing!
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ResolutionResult(BaseModel):
    is_resolved: bool
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    resolved_entity_type: Optional[str] = None  # DOCTOR, SLOT, APPOINTMENT, DATE
    resolved_data: Dict[str, Any] = {}


class ContextResolver:
    
    @staticmethod
    def resolve_doctor_reference(
        user_utterance: str,
        last_doctor_name: Optional[str],
        last_doctor_id: Optional[str]
    ) -> ResolutionResult:
        """
        Resolves phrases like "Same doctor as last time" or "Dr. Sharma again".
        """
        lowered = user_utterance.lower()
        if "same doctor" in lowered or "last time" in lowered or "previous doctor" in lowered:
            if last_doctor_id and last_doctor_name:
                return ResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="DOCTOR",
                    resolved_data={
                        "doctor_id": last_doctor_id,
                        "doctor_name": last_doctor_name,
                        "source": "LONG_TERM_PROFILE"
                    }
                )
            else:
                return ResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question="I don't have a record of your previous doctor on file. Which doctor or specialty would you like to see?"
                )
        return ResolutionResult(is_resolved=False)

    @staticmethod
    def resolve_slot_reference(
        user_utterance: str,
        available_slots_in_session: List[Dict[str, Any]]
    ) -> ResolutionResult:
        """
        Resolves phrases like "Book that one", "The first one", "The afternoon slot".
        """
        lowered = user_utterance.lower()
        if "that one" in lowered or "first one" in lowered:
            if len(available_slots_in_session) == 1:
                return ResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="SLOT",
                    resolved_data=available_slots_in_session[0]
                )
            elif len(available_slots_in_session) > 1:
                return ResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question=f"I found multiple available slots. Did you mean the slot at {available_slots_in_session[0].get('start_time')} or another time?"
                )
            else:
                return ResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question="I haven't searched for available slots yet. Which doctor or day would you like me to check?"
                )
        return ResolutionResult(is_resolved=False)

    @staticmethod
    def resolve_appointment_cancellation(
        user_utterance: str,
        active_appointments: List[Dict[str, Any]]
    ) -> ResolutionResult:
        """
        Resolves "Cancel my upcoming appointment".
        """
        lowered = user_utterance.lower()
        if "cancel" in lowered and ("appointment" in lowered or "upcoming" in lowered):
            if len(active_appointments) == 1:
                appt = active_appointments[0]
                return ResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="APPOINTMENT",
                    resolved_data={"appointment_id": appt["id"], "doctor_name": appt.get("doctor_name")}
                )
            elif len(active_appointments) > 1:
                options = ", ".join([f"Dr. {a.get('doctor_name')} on {a.get('start_datetime')}" for a in active_appointments])
                return ResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question=f"You have multiple upcoming appointments ({options}). Which one would you like to cancel?"
                )
            else:
                return ResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question="You don't currently have any scheduled upcoming appointments."
                )
        return ResolutionResult(is_resolved=False)
