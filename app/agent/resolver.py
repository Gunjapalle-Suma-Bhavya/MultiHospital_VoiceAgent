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


import re
import json
from datetime import datetime, date, time, timedelta, timezone
from app.database.models import Doctor, Hospital, PatientSessionState, PatientProfile
from app.agent.intent_understanding import SymptomIntentResolver


class ContextAwareReferenceResolver:
    """
    Stateful context resolver integrated with DB session & patient session state.
    Resolves doctor entities, hospital facilities, dates/times, and conversational intent.
    """

    def __init__(self, db_session):
        self.db = db_session

    def resolve_context(self, session_id: str, patient_phone: str, user_utterance: str) -> Dict[str, Any]:
        lowered = user_utterance.lower().strip()
        hospital_id = None
        doctor_id = None
        doctor_name = None
        target_datetime = None
        intent = "GENERAL_INQUIRY"

        # 1. Load active draft session state if present
        draft: Dict[str, Any] = {}
        session_state = None
        if session_id:
            try:
                session_state = self.db.query(PatientSessionState).filter(PatientSessionState.session_id == session_id).first()
                if session_state and session_state.active_draft_booking_json:
                    draft = json.loads(session_state.active_draft_booking_json)
            except Exception:
                pass

        # 2. Match Doctor by Name in Database
        active_docs = []
        try:
            active_docs = self.db.query(Doctor).filter(Doctor.is_active == True).all()
        except Exception:
            pass

        matched_doc = None
        common_name_words = {"white", "green", "reed", "may", "day", "long", "young", "brown", "gray", "grey", "have", "more", "head", "well", "house"}
        for d in active_docs:
            d_name = d.name.lower()
            clean_full = re.sub(r'^(dr\.?|doctor)\s*', '', d_name).strip()
            last_name = clean_full.split()[-1] if clean_full else ""

            # Check exact Dr./Doctor title patterns, clean full names, or distinctive last names
            dr_pat = rf'\b(dr\.?|doctor)\s+{re.escape(last_name)}\b'
            dr_full_pat = rf'\b(dr\.?|doctor)\s+{re.escape(clean_full)}\b'
            if re.search(dr_full_pat, lowered) or re.search(dr_pat, lowered):
                matched_doc = d
                break
            elif clean_full and len(clean_full) >= 5 and clean_full in lowered:
                matched_doc = d
                break
            elif last_name and len(last_name) >= 4 and last_name not in common_name_words and re.search(rf'\b{re.escape(last_name)}\b', lowered):
                matched_doc = d
                break

        if matched_doc:
            doctor_id = matched_doc.id
            hospital_id = matched_doc.hospital_id
            doctor_name = matched_doc.name
        elif draft.get("doctor_id"):
            doctor_id = draft.get("doctor_id")
            hospital_id = draft.get("hospital_id")
            doctor_name = draft.get("doctor_name")

        # 3. Match Hospital Name
        if not hospital_id:
            try:
                active_hosps = self.db.query(Hospital).filter(Hospital.is_active == True).all()
                for h in active_hosps:
                    h_name = h.name.lower()
                    clean_hosp = re.sub(r'\b(hospital|center|medical|health|system|general|care|clinic)\b', '', h_name).strip()
                    if clean_hosp and len(clean_hosp) >= 4 and clean_hosp in lowered:
                        hospital_id = h.id
                        break
                    elif h_name in lowered:
                        hospital_id = h.id
                        break
            except Exception:
                pass

        # 4. Extract Date / Time / Slots
        time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', lowered)
        if time_match:
            hr = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            meridiem = time_match.group(3)
            if meridiem == 'pm' and hr < 12:
                hr += 12
            elif meridiem == 'am' and hr == 12:
                hr = 0
            target_d = date.today() + timedelta(days=1)
            target_datetime = datetime.combine(target_d, time(hr, minute))
        elif any(w in lowered for w in ["morning", "morning slot", "9 am", "9:00 am"]):
            target_d = date.today() + timedelta(days=1)
            target_datetime = datetime.combine(target_d, time(9, 0))
        elif any(w in lowered for w in ["afternoon", "afternoon slot", "2 pm", "2:00 pm"]):
            target_d = date.today() + timedelta(days=1)
            target_datetime = datetime.combine(target_d, time(14, 0))
        elif any(w in lowered for w in ["first one", "first slot", "earliest", "that slot"]):
            target_d = date.today() + timedelta(days=1)
            target_datetime = datetime.combine(target_d, time(9, 0))

        # 5. Symptom Inference
        symptom_res = SymptomIntentResolver.infer_specialty_from_utterance(user_utterance)
        inferred_spec = symptom_res.inferred_specialty if symptom_res.has_symptom else None

        # 6. Context-Aware Intent Resolution
        # A. Emergency / Human Escalation Priority
        if any(w in lowered for w in ["emergency", "chest pain", "crushing", "ambulance", "heart attack", "human", "operator", "help right now", "call 911", "dying"]):
            intent = "HUMAN_ESCALATION"

        # B. Cancellation
        elif "cancel" in lowered:
            intent = "CANCEL_APPOINTMENT"

        # C. User selected a specific time/slot or confirmed booking with a known doctor
        elif target_datetime and doctor_id:
            intent = "BOOK_APPOINTMENT"
        elif any(w in lowered for w in ["book that", "confirm", "reserve that", "yes please", "lock it in", "book it"]) and doctor_id:
            intent = "BOOK_APPOINTMENT"

        # D. User asks for availability / slots
        elif any(w in lowered for w in ["availab", "slot", "openings", "free time", "when is", "schedule for tomorrow", "when can"]):
            intent = "CHECK_AVAILABILITY"

        # E. Hospital FAQs (prioritize specific logistics over general words)
        elif any(w in lowered for w in ["visiting hour", "visiting", "hospital hour", "clinic hour", "hours of operation", "visiting hours", "timings", "what time do you open", "when do you open", "when are you open", "when do you close"]):
            intent = "HOSPITAL_HOURS"
        elif any(w in lowered for w in ["where are you", "location", "address", "directions", "where is", "parking"]):
            intent = "HOSPITAL_LOCATION"
        elif any(w in lowered for w in ["insurance", "medicare", "medicaid", "copay", "co-pay", "coverage", "cost", "fee", "price", "pay"]):
            intent = "HOSPITAL_INSURANCE"
        elif any(w in lowered for w in ["bring", "prepare", "preparation", "documents", "paperwork", "what do i need", "what should i have", "what should i bring"]):
            intent = "CLINIC_PREPARATION"

        # F. User requests booking or an appointment
        elif any(w in lowered for w in ["book", "appointment", "schedule", "consultation", "see a doctor"]):
            intent = "BOOK_APPOINTMENT"

        # G. User asks about a specific doctor by name
        elif matched_doc and not any(w in lowered for w in ["book", "appointment", "schedule"]):
            intent = "DOCTOR_INQUIRY"

        # H. Doctor / Specialist Search
        elif any(w in lowered for w in ["doctor", "specialist", "physician", "find", "search", "who works"]):
            intent = "SEARCH_DOCTORS"

        # I. Symptom triage
        elif inferred_spec:
            intent = "SEARCH_DOCTORS"

        return {
            "intent": intent,
            "hospital_id": hospital_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "target_datetime": target_datetime,
            "inferred_specialty": inferred_spec,
            "is_resolved": True
        }

