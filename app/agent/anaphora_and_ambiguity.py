"""
Context Resolution (Section 5.18) & Ambiguity Handling Engine (Section 5.19).

Resolves conversational references:
- "Book that doctor." -> Resolves to active or preferred doctor in context state.
- "Actually Friday." -> Updates date in active conversation state while retaining doctor/hospital.
- "Same hospital as last time." -> Resolves to last hospital in Tier 3 context.
- "Cancel my upcoming appointment." -> Resolves active appointment; prompts for clarification if multiple exist.

Enforces zero-guessing ambiguity rules:
- Prompts for missing required parameters.
- Asks for clarification when multiple candidates match (e.g. 2 doctors or 2 appointments).
- Suggests alternatives when no matching slots exist.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agent.multi_tier_context import HierarchicalContextBundle, MultiTierContextEngine
from app.agent.conversation_state import ConversationStateManager


class ContextResolutionResult(BaseModel):
    is_resolved: bool
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    resolved_entity_type: Optional[str] = None  # DOCTOR, HOSPITAL, SLOT, APPOINTMENT, DATE
    resolved_data: Dict[str, Any] = {}
    suggested_alternatives: List[Dict[str, Any]] = []


class AnaphoraContextResolver:
    """
    Resolves anaphoric and conversational references against 4-tier context bundle (Section 5.18).
    """

    @staticmethod
    def resolve_reference(
        user_utterance: str,
        context_bundle: HierarchicalContextBundle
    ) -> ContextResolutionResult:
        lowered = user_utterance.lower().strip()

        # 1. "Same hospital as last time"
        if "same hospital" in lowered or "last hospital" in lowered:
            hospitals = context_bundle.tier3_long_term.preferred_hospitals
            if hospitals:
                return ContextResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="HOSPITAL",
                    resolved_data={"hospital_name": hospitals[0], "source": "TIER_3_LONG_TERM_PREFERENCE"}
                )
            else:
                return ContextResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question="I don't have a record of your previous hospital on file. Which hospital would you like to visit?"
                )

        # 2. "Book that doctor" / "Book him" / "Book her"
        if "that doctor" in lowered or "book him" in lowered or "book her" in lowered:
            sel_doc = context_bundle.tier1_conversation_state.selected_doctor
            pref_docs = context_bundle.tier3_long_term.preferred_doctors
            if sel_doc:
                return ContextResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="DOCTOR",
                    resolved_data={"doctor": sel_doc, "source": "TIER_1_CONVERSATION_STATE"}
                )
            elif pref_docs:
                return ContextResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="DOCTOR",
                    resolved_data={"doctor_name": pref_docs[0], "source": "TIER_3_LONG_TERM_PREFERENCE"}
                )
            else:
                return ContextResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question="Which doctor would you like to book an appointment with?"
                )

        # 3. "Actually Friday" / "Actually next Monday"
        if "actually" in lowered and any(day in lowered for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            target_day = next(day for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] if day in lowered)
            return ContextResolutionResult(
                is_resolved=True,
                resolved_entity_type="DATE",
                resolved_data={
                    "updated_date_day": target_day.capitalize(),
                    "retained_specialty": context_bundle.tier1_conversation_state.specialty,
                    "retained_doctor": context_bundle.tier1_conversation_state.selected_doctor,
                    "retained_hospital": context_bundle.tier1_conversation_state.selected_hospital
                }
            )

        # 4. "Cancel my upcoming appointment"
        if "cancel" in lowered and ("appointment" in lowered or "upcoming" in lowered):
            appts = context_bundle.tier4_appointment_info.upcoming_appointments
            if len(appts) == 1:
                return ContextResolutionResult(
                    is_resolved=True,
                    resolved_entity_type="APPOINTMENT",
                    resolved_data=appts[0]
                )
            elif len(appts) > 1:
                formatted_list = [f"{i+1}) {a['doctor_name']} at {a['hospital_name']} on {a['start_datetime']}" for i, a in enumerate(appts)]
                prompt_msg = f"I see you have {len(appts)} upcoming appointments:\n" + "\n".join(formatted_list) + "\nWhich appointment would you like to cancel?"
                return ContextResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question=prompt_msg
                )
            else:
                return ContextResolutionResult(
                    is_resolved=False,
                    requires_clarification=True,
                    clarification_question="You do not have any active upcoming appointments to cancel."
                )

        return ContextResolutionResult(is_resolved=False)


class AmbiguityClarificationEngine:
    """
    Detects ambiguity and generates explicit clarification questions (Section 5.19).
    """

    @staticmethod
    def evaluate_ambiguity(
        intent: str,
        matching_doctors: List[Dict[str, Any]],
        available_slots: List[Dict[str, Any]],
        requested_date: Optional[str] = None,
        requested_time_window: Optional[str] = None
    ) -> ContextResolutionResult:

        # Case 1: Multiple matching doctors for a specialty request
        if len(matching_doctors) > 1:
            names = [d.get("name", "Doctor") for d in matching_doctors[:3]]
            doc_str = " or ".join(names)
            question = f"I found {len(matching_doctors)} doctors available. Would you prefer {doc_str}?"
            return ContextResolutionResult(
                is_resolved=False,
                requires_clarification=True,
                clarification_question=question,
                suggested_alternatives=matching_doctors
            )

        # Case 2: No slots available for requested time window/date -> offer alternative
        if len(available_slots) == 0 and requested_date and requested_time_window:
            question = f"There are no {requested_time_window.lower()} appointments available on {requested_date}. Would you like me to check Friday or try a morning slot?"
            return ContextResolutionResult(
                is_resolved=False,
                requires_clarification=True,
                clarification_question=question,
                suggested_alternatives=[{"suggested_date": "Friday", "suggested_time_window": "MORNING"}]
            )

        # Case 3: Ambiguous relative date phrase ("next Thursday")
        if requested_date and "next thursday" in requested_date.lower():
            question = "Just to confirm, did you mean this coming Thursday or Thursday of next week?"
            return ContextResolutionResult(
                is_resolved=False,
                requires_clarification=True,
                clarification_question=question
            )

        return ContextResolutionResult(is_resolved=True)
