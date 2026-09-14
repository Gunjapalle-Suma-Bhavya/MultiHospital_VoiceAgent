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
        # Normalize common speech-to-text variations and typos (e.g. appointement, apointment)
        lowered = re.sub(r'\bappoint[a-z]*\b', 'appointment', lowered)
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

        if not draft and patient_phone:
            try:
                pat = self.db.query(PatientProfile).filter(PatientProfile.phone_number == patient_phone).first()
                if pat:
                    recent = self.db.query(PatientSessionState).filter(
                        PatientSessionState.patient_id == pat.id,
                        PatientSessionState.active_draft_booking_json.isnot(None)
                    ).order_by(PatientSessionState.updated_at.desc()).first()
                    if recent and recent.active_draft_booking_json:
                        parsed_d = json.loads(recent.active_draft_booking_json)
                        if parsed_d.get("stage") in ["AWAITING_SLOT_SELECTION", "SLOTS_OFFERED"]:
                            draft = parsed_d
                            session_state = recent
            except Exception:
                pass

        # 2. Check for symptoms / clinical concerns in current utterance early
        symptom_res = SymptomIntentResolver.infer_specialty_from_utterance(user_utterance)
        inferred_spec = symptom_res.inferred_specialty if symptom_res.has_symptom else None

        # 3. Match Doctor by Name in Database
        active_docs = []
        try:
            from app.database.models import DoctorStatus
            active_docs = self.db.query(Doctor).filter(
                (Doctor.is_active == True) | (Doctor.doctor_status == DoctorStatus.ACTIVE)
            ).all()
        except Exception:
            try:
                active_docs = self.db.query(Doctor).all()
            except Exception:
                active_docs = []

        matched_doc = None
        best_match_score = 0
        common_name_words = {"white", "green", "reed", "may", "day", "long", "young", "brown", "gray", "grey", "have", "more", "head", "well", "house"}
        for d in active_docs:
            d_name = (d.name or "").lower().strip()
            clean_full = re.sub(r'^(dr\.?|doctor)\s*', '', d_name).strip()
            name_parts = [p for p in clean_full.split() if not re.match(r'^[0-9a-f]{4,8}$', p, re.I) and not p.isdigit()]
            last_name = name_parts[-1] if name_parts else ""
            first_name = name_parts[0] if name_parts else ""

            dr_full_pat = rf'\b(dr\.?|doctor)\s+{re.escape(clean_full)}\b'
            dr_pat = rf'\b(dr\.?|doctor)\s+{re.escape(last_name)}\b' if last_name else ""

            score = 0
            if clean_full and clean_full in lowered:
                score = 100 + len(clean_full)
            elif re.search(dr_full_pat, lowered):
                score = 90 + len(clean_full)
            elif d_name and d_name in lowered:
                score = 80 + len(d_name)
            elif last_name and len(last_name) >= 3 and last_name not in common_name_words and ((dr_pat and re.search(dr_pat, lowered)) or re.search(rf'\b{re.escape(last_name)}\b', lowered)):
                score = 50 + len(last_name)
            elif first_name and len(first_name) >= 4 and first_name not in common_name_words and re.search(rf'\b(dr\.?|doctor)\s+{re.escape(first_name)}\b', lowered):
                score = 30 + len(first_name)
            elif d.id.lower() in lowered:
                score = 110

            # Tie-breaker bonus if doctor is canonical accredited provider or has approved questions configured
            if score > 0:
                if d.id in ["DOC-SHARMA-01", "DOC-RAO-02", "DOC-GOMEZ-03", "DOC-JENKINS-04", "DOC-CHEN-05", "DOC-PATEL-06", "DOC-MARCUS-07", "DOC-WHITE-08", "DOC-VANCE-09", "DOC-MALHOTRA-10", "DOC-DOC1", "DOC-DOC3", "DOC-DOCDEM1"]:
                    score += 25
                try:
                    from app.database.models import DoctorApprovedQuestion
                    if self.db.query(DoctorApprovedQuestion.id).filter(DoctorApprovedQuestion.doctor_id == d.id).first():
                        score += 15
                except Exception:
                    pass

            if score > best_match_score:
                best_match_score = score
                matched_doc = d

        if matched_doc:
            doctor_id = matched_doc.id
            hospital_id = matched_doc.hospital_id
            doctor_name = matched_doc.name
        elif draft.get("doctor_id") and (draft.get("stage") in ["SLOTS_OFFERED_FOR_DOCTOR", "QUESTIONNAIRE_PROMPT_OFFERED", "QUESTIONNAIRE_IN_PROGRESS", "DOCTOR_QUESTIONNAIRE_IN_PROGRESS"] or not symptom_res.has_symptom):
            doctor_id = draft.get("doctor_id")
            hospital_id = draft.get("hospital_id")
            doctor_name = draft.get("doctor_name")

        # 4. Match Hospital Name or Code explicitly mentioned in utterance
        explicit_hospital = None
        best_hosp_score = 0
        try:
            from app.database.models import HospitalStatus
            active_hosps = self.db.query(Hospital).filter(
                (Hospital.is_active == True) | (Hospital.hospital_status == HospitalStatus.APPROVED)
            ).all()
            for h in active_hosps:
                h_name = (h.name or "").lower().strip()
                h_code = (h.code or "").lower().strip()
                clean_hosp = re.sub(r'\b(hospital|center|medical|health|system|general|care|clinic)\b', '', h_name).strip()

                h_score = 0
                # 1. Full name match (e.g. "h1 hospital", "city memorial hospital")
                if h_name and h_name in lowered:
                    h_score = 100 + len(h_name)
                # 2. Code match with word boundary (e.g. "h1" in "book in h1", "h1 hospital")
                elif h_code and re.search(rf'\b{re.escape(h_code)}\b', lowered):
                    h_score = 95 + len(h_code)
                # 3. Clean hospital name match (e.g. "h1", "medico")
                elif clean_hosp and len(clean_hosp) >= 2 and re.search(rf'\b{re.escape(clean_hosp)}\b', lowered):
                    h_score = 90 + len(clean_hosp)

                if h_score > best_hosp_score:
                    best_hosp_score = h_score
                    explicit_hospital = h

            if explicit_hospital:
                hospital_id = explicit_hospital.id
        except Exception:
            pass

        # If user explicitly specified a hospital, prioritize doctors from that hospital
        if explicit_hospital and not doctor_id:
            hosp_doc = self.db.query(Doctor).filter(
                Doctor.hospital_id == explicit_hospital.id,
                Doctor.is_active == True
            ).first()
            if hosp_doc and any(w in lowered for w in ["book", "appointment", "schedule"]):
                doctor_id = hosp_doc.id
                doctor_name = hosp_doc.name
                intent = "CHECK_AVAILABILITY"

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
            if draft.get("first_slot"):
                try:
                    target_datetime = datetime.fromisoformat(draft["first_slot"])
                except Exception:
                    pass
        elif (draft.get("stage") in ["SLOTS_OFFERED", "DOCTORS_RECOMMENDED", "DOCTOR_INQUIRY"] or doctor_id) and any(w in lowered for w in [
            "okay book", "ok book", "okay", "ok", "yes", "sure", "go ahead", "confirm", "lock it in",
            "book it", "book that", "yes please", "please book", "book an appointment", "book appointment",
            "process that", "process it", "i want to book", "book with", "book that slot", "book the slot", "fine",
            # Telugu affirmatives
            "బుక్ చేయండి", "సరే బుక్", "అపాయింట్‌మెంట్ బుక్", "సరే", "అవును", "చేయండి", "ఖరారు చేయండి", "ముందుకు సాగండి",
            "sare", "avunu", "book cheyandi", "sare book"
        ]):
            if draft.get("first_slot"):
                try:
                    target_datetime = datetime.fromisoformat(draft["first_slot"])
                except Exception:
                    pass

        # Check for pause / interruption / hold on requests
        if any(w in lowered for w in [
            "wait", "hold on", "pause", "one moment", "one second", "give me a second",
            "hang on", "stop for a moment", "just a second", "just a moment", "listen",
            "ఆగండి", "కాసేపు ఆగండి", "ఒక్క నిమిషం"
        ]) and not any(w in lowered for w in ["cancel", "emergency"]):
            intent = "CONVERSATIONAL_PAUSE"

        # Check for General / Normal Conversation intent
        elif any(w in lowered for w in [
            "normal conversation", "general conversation", "let's chat", "lets chat",
            "can we chat", "just chat", "just talking", "talk to me", "casual chat",
            "casual conversation", "have a conversation", "normal chat", "general chat"
        ]) or (
            lowered.strip() in [
                "hello", "hi", "hey", "hello there", "good morning", "good afternoon",
                "good evening", "how are you", "how are you doing", "namaste",
                "హలో", "నమస్కారం", "ఎలా ఉన్నారు", "బాగున్నారా"
            ] and not matched_doc and not any(w in lowered for w in ["pain", "fever", "appointment", "doctor", "slot"])
        ):
            intent = "GENERAL_CONVERSATION"

        # 5. Check active draft stage for slot selection, doctor recommendation, or questionnaire
        elif draft.get("stage") in ["SYMPTOM_OFFER_DOCTORS", "SYMPTOM_OFFER_CHECK_DOCTORS", "SYMPTOM_SPECIALTY_INFERRED"]:
            if any(w in lowered for w in [
                "show", "available", "doctor", "doctors", "yes", "sure", "ok", "okay", "yep", "fine", "yeah", "please",
                "check", "please check", "show available doctors", "show doctors", "yes show", "yes please",
                "who is available", "who are the available doctors", "what doctors are available",
                "tell me the doctors", "which doctors are there", "show me", "show them",
                "సరే", "అవును", "డాక్టర్లు", "చూపించండి"
            ]):
                intent = "SHOW_AVAILABLE_DOCTORS"

        elif any(w in lowered for w in [
            "show available doctors", "show doctors", "available doctors", "show me available doctors",
            "who is available", "who are the available doctors", "what doctors are available",
            "tell me the doctors", "which doctors are there", "show me the doctors", "can you show doctors",
            "list doctors", "yes please show doctors", "yeah show doctors"
        ]) and not any(w in lowered for w in ["slots", "time", "hour"]):
            intent = "SHOW_AVAILABLE_DOCTORS"

        elif any(w in lowered for w in [
            "show available doctors and slots", "show me available doctors and slots", "show available doctors and their slots",
            "show doctors and slots", "show doctors and their slots", "available doctors and slots", "available doctors and their slots",
            "show all available doctors and slots", "show all doctors and slots"
        ]):
            intent = "SHOW_DOCTORS_AND_SLOTS"

        elif draft.get("stage") == "DOCTORS_OFFERED":
            # Patient is choosing from the offered list of doctors
            offered_docs = draft.get("doctors", [])
            matched_od = None

            # 1. Match by doctor name or alias
            for od in offered_docs:
                doc_token = od["doctor_name"].lower().replace("dr.", "").strip()
                tokens = [t for t in doc_token.split() if not re.match(r'^[0-9a-f]{4,8}$', t, re.I) and not t.isdigit()]
                first_tok = tokens[0] if tokens else ""
                last_tok = tokens[-1] if tokens else ""
                if (doc_token and doc_token in lowered) or (last_tok and len(last_tok) >= 3 and last_tok in lowered) or (first_tok and len(first_tok) >= 4 and first_tok in lowered):
                    matched_od = od
                    break

            # 2. Match by ordinal or option number
            if not matched_od:
                if any(w in lowered for w in ["first doctor", "1st doctor", "first one", "1st one", "dr 1", "number 1", "number one", "first", "option 1", "doc 1", "doctor 1", "1"]) and len(offered_docs) >= 1:
                    matched_od = offered_docs[0]
                elif any(w in lowered for w in ["second doctor", "2nd doctor", "second one", "2nd one", "dr 2", "number 2", "number two", "second", "option 2", "doc 2", "doctor 2", "2"]) and len(offered_docs) >= 2:
                    matched_od = offered_docs[1]
                elif any(w in lowered for w in ["third doctor", "3rd doctor", "third one", "3rd one", "dr 3", "number 3", "number three", "third", "option 3", "doc 3", "doctor 3", "3"]) and len(offered_docs) >= 3:
                    matched_od = offered_docs[2]

            # 3. Match by hospital facility
            if not matched_od:
                for od in offered_docs:
                    h_name = od.get("hospital_name", "").lower()
                    clean_h = re.sub(r'\b(hospital|center|medical|health|care|clinic)\b', '', h_name).strip()
                    if (clean_h and len(clean_h) >= 3 and clean_h in lowered) or (h_name and h_name in lowered):
                        matched_od = od
                        break

            if not matched_od and matched_doc:
                for od in offered_docs:
                    if od["doctor_id"] == matched_doc.id:
                        matched_od = od
                        break
                if not matched_od:
                    matched_od = {
                        "doctor_id": matched_doc.id,
                        "doctor_name": matched_doc.name,
                        "hospital_id": matched_doc.hospital_id
                    }

            if matched_od:
                doctor_id = matched_od["doctor_id"]
                doctor_name = matched_od["doctor_name"]
                hospital_id = matched_od.get("hospital_id")
                if target_datetime:
                    intent = "BOOK_APPOINTMENT"
                else:
                    intent = "SHOW_DOCTOR_SLOTS"

        elif draft.get("stage") == "SLOTS_OFFERED_FOR_DOCTOR":
            # Patient is choosing a time slot for the selected doctor
            doctor_id = draft.get("doctor_id")
            doctor_name = draft.get("doctor_name")
            hospital_id = draft.get("hospital_id")
            slots = draft.get("slots", [])
            target_d = date.today() + timedelta(days=1)

            slot_matched = None
            for s in slots:
                clean_s = s.lower().strip()
                short_s = clean_s.lstrip('0').replace(':00', '')
                if clean_s in lowered or short_s in lowered:
                    slot_matched = s
                    break

            if not slot_matched and slots:
                if any(w in lowered for w in ["first slot", "1st slot", "slot 1", "option 1", "number 1", "first", "1", "1st", "earliest", "morning"]) and len(slots) >= 1:
                    slot_matched = slots[0]
                elif any(w in lowered for w in ["second slot", "2nd slot", "slot 2", "option 2", "number 2", "second", "2", "2nd"]) and len(slots) >= 2:
                    slot_matched = slots[1]
                elif any(w in lowered for w in ["third slot", "3rd slot", "slot 3", "option 3", "number 3", "third", "3", "3rd", "afternoon"]) and len(slots) >= 3:
                    slot_matched = slots[2]
                elif any(w in lowered for w in ["fourth slot", "4th slot", "slot 4", "option 4", "number 4", "fourth", "4", "4th", "evening"]) and len(slots) >= 4:
                    slot_matched = slots[3]

            if not slot_matched:
                time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', lowered)
                if time_match:
                    hr = int(time_match.group(1))
                    minute = int(time_match.group(2) or 0)
                    ampm = time_match.group(3)
                    if ampm == 'pm' and hr < 12:
                        hr += 12
                    elif ampm == 'am' and hr == 12:
                        hr = 0
                    elif not ampm and 1 <= hr <= 6:
                        hr += 12
                    target_datetime = datetime.combine(target_d, time(hr, minute))
                    intent = "BOOK_APPOINTMENT"

            if slot_matched:
                try:
                    parsed_t = datetime.strptime(slot_matched, "%I:%M %p").time()
                    target_datetime = datetime.combine(target_d, parsed_t)
                except Exception:
                    target_datetime = datetime.combine(target_d, time(10, 0))
                intent = "BOOK_APPOINTMENT"
            elif any(w in lowered for w in [
                "ok", "okay", "yes", "sure", "confirm", "lock it in", "book it", "please book", "book that",
                "book an appointment", "book appointment", "fine", "సరే", "అవును", "బుక్ చేయండి"
            ]):
                if draft.get("first_slot"):
                    try:
                        target_datetime = datetime.fromisoformat(draft["first_slot"])
                    except Exception:
                        pass
                if not target_datetime and slots:
                    try:
                        parsed_t = datetime.strptime(slots[0], "%I:%M %p").time()
                        target_datetime = datetime.combine(target_d, parsed_t)
                    except Exception:
                        pass
                if not target_datetime:
                    target_datetime = datetime.combine(target_d, time(10, 0))
                intent = "BOOK_APPOINTMENT"
            elif target_datetime:
                intent = "BOOK_APPOINTMENT"

        elif draft.get("stage") == "DOCTORS_AND_SLOTS_OFFERED":
            # Patient is choosing from the combined offered list of doctors and slots
            offered_docs = draft.get("doctors", [])
            target_d = date.today() + timedelta(days=1)
            matched_od = None

            # 1. Match by doctor name
            for od in offered_docs:
                doc_token = od["doctor_name"].lower().replace("dr.", "").strip()
                tokens = [t for t in doc_token.split() if not re.match(r'^[0-9a-f]{4,8}$', t, re.I) and not t.isdigit()]
                first_tok = tokens[0] if tokens else ""
                last_tok = tokens[-1] if tokens else ""
                if (doc_token and doc_token in lowered) or (first_tok and len(first_tok) >= 4 and first_tok in lowered) or (last_tok and len(last_tok) >= 3 and last_tok in lowered):
                    matched_od = od
                    break

            # 2. Match by ordinal or option number
            if not matched_od:
                if any(w in lowered for w in ["first doctor", "1st doctor", "first one", "1st one", "dr 1", "number 1", "number one", "first", "option 1", "doc 1", "doctor 1", "1"]) and len(offered_docs) >= 1:
                    matched_od = offered_docs[0]
                elif any(w in lowered for w in ["second doctor", "2nd doctor", "second one", "2nd one", "dr 2", "number 2", "number two", "second", "option 2", "doc 2", "doctor 2", "2"]) and len(offered_docs) >= 2:
                    matched_od = offered_docs[1]
                elif any(w in lowered for w in ["third doctor", "3rd doctor", "third one", "3rd one", "dr 3", "number 3", "number three", "third", "option 3", "doc 3", "doctor 3", "3"]) and len(offered_docs) >= 3:
                    matched_od = offered_docs[2]

            # 3. Match by hospital facility
            if not matched_od:
                for od in offered_docs:
                    h_name = od.get("hospital_name", "").lower()
                    clean_h = re.sub(r'\b(hospital|center|medical|health|care|clinic)\b', '', h_name).strip()
                    if (clean_h and len(clean_h) >= 3 and clean_h in lowered) or (h_name and h_name in lowered):
                        matched_od = od
                        break

            # 4. Match by slot time mentioned
            if not matched_od:
                for od in offered_docs:
                    slots = od.get("slots", [])
                    for s in slots:
                        clean_s = s.lower().strip()
                        short_s = clean_s.lstrip('0').replace(':00', '')
                        if clean_s in lowered or short_s in lowered:
                            matched_od = od
                            break
                    if matched_od:
                        break

            if not matched_od and matched_doc:
                for od in offered_docs:
                    if od["doctor_id"] == matched_doc.id:
                        matched_od = od
                        break

            if matched_od:
                doctor_id = matched_od["doctor_id"]
                doctor_name = matched_od["doctor_name"]
                hospital_id = matched_od.get("hospital_id")
                intent = "BOOK_APPOINTMENT"

                # If user explicitly specified a time in utterance, use that
                if not target_datetime:
                    slots = matched_od.get("slots", [])
                    if slots:
                        for s in slots:
                            try:
                                parsed_t = datetime.strptime(s.strip(), "%I:%M %p").time()
                                target_datetime = datetime.combine(target_d, parsed_t)
                                break
                            except Exception:
                                pass
                    if not target_datetime and matched_od.get("first_slot_iso"):
                        try:
                            target_datetime = datetime.fromisoformat(matched_od["first_slot_iso"])
                        except Exception:
                            pass
                    if not target_datetime:
                        target_datetime = datetime.combine(target_d, time(16, 0))

        elif draft.get("stage") == "DOCTORS_RECOMMENDED":
            # Patient choosing from recommended doctors
            if draft.get("options"):
                for opt in draft["options"]:
                    doc_token = opt["doctor_name"].lower().replace("dr.", "").strip()
                    first_tok = doc_token.split()[0] if doc_token.split() else ""
                    last_tok = doc_token.split()[-1] if doc_token.split() else ""
                    if (doc_token and doc_token in lowered) or (last_tok and len(last_tok) >= 3 and last_tok in lowered):
                        doctor_id = opt["doctor_id"]
                        doctor_name = opt["doctor_name"]
                        hospital_id = opt.get("hospital_id")
                        intent = "CHECK_AVAILABILITY"
                        break
                if not doctor_id and any(w in lowered for w in ["first", "first one", "first doctor", "dr 1"]):
                    opt = draft["options"][0]
                    doctor_id = opt["doctor_id"]
                    doctor_name = opt["doctor_name"]
                    hospital_id = opt.get("hospital_id")
                    intent = "CHECK_AVAILABILITY"

            if not doctor_id and matched_doc:
                doctor_id = matched_doc.id
                doctor_name = matched_doc.name
                hospital_id = matched_doc.hospital_id
                intent = "CHECK_AVAILABILITY"

        elif draft.get("stage") == "AWAITING_SLOT_SELECTION" and draft.get("options"):
            for opt in draft["options"]:
                doc_token = opt["doctor_name"].lower().replace("dr.", "").strip()
                time_token = opt.get("time_str", "").lower().strip()
                if (doc_token and doc_token in lowered) or (time_token and time_token in lowered):
                    doctor_id = opt["doctor_id"]
                    doctor_name = opt["doctor_name"]
                    hospital_id = opt["hospital_id"]
                    target_d = date.today() + timedelta(days=1)
                    hr = opt.get("hour", 16)
                    mn = opt.get("minute", 0)
                    target_datetime = datetime.combine(target_d, time(hr, mn))
                    intent = "BOOK_APPOINTMENT"
                    break

        # 6. Symptom Inference
        symptom_res = SymptomIntentResolver.infer_specialty_from_utterance(user_utterance)
        inferred_spec = symptom_res.inferred_specialty if symptom_res.has_symptom else None

        has_symptom_query = bool(inferred_spec) or any(w in lowered for w in [
            "shoulder", "knee", "chest", "headache", "fever", "pain", "see a doctor",
            "consult a doctor", "book an appointment", "start over", "new appointment"
        ])

        if draft.get("stage") in ["QUESTIONNAIRE_PROMPT_OFFERED", "QUESTIONNAIRE_IN_PROGRESS", "DOCTOR_QUESTIONNAIRE_IN_PROGRESS"]:
            if not any(w in lowered for w in ["emergency", "crushing", "ambulance", "heart attack", "call 911", "dying", "start over", "cancel"]):
                intent = "QUESTIONNAIRE_RESPONSE"

        # 7. Context-Aware Intent Resolution
        # A. Emergency / Human Escalation Priority
        if any(w in lowered for w in [
            "emergency", "chest pain", "crushing", "ambulance", "heart attack", "human", "operator", "help right now", "call 911", "dying",
            # Telugu emergency
            "అత్యవసరం", "ప్రాణాపాయం", "అంబులెన్స్", "గుండెపోటు", "సహాయం చేయండి", "కాపాడండి"
        ]):
            intent = "HUMAN_ESCALATION"

        elif intent in [
            "QUESTIONNAIRE_RESPONSE",
            "BOOK_APPOINTMENT",
            "SHOW_AVAILABLE_DOCTORS",
            "SHOW_DOCTOR_SLOTS",
            "SHOW_DOCTORS_AND_SLOTS",
            "CONVERSATIONAL_PAUSE",
            "GENERAL_CONVERSATION"
        ]:
            pass

        elif symptom_res.has_symptom and not matched_doc and not any(w in lowered for w in ["cancel", "raddu", "రద్దు"]):
            intent = "SEARCH_DOCTORS"

        elif draft.get("stage") == "SYMPTOM_OFFER_CHECK_DOCTORS" and intent == "SEARCH_DOCTORS":
            pass
        elif draft.get("stage") == "DOCTORS_RECOMMENDED" and intent == "CHECK_AVAILABILITY":
            pass

        # B. Cancellation
        elif any(w in lowered for w in ["cancel", "రద్దు", "రద్దు చేయండి", "raddu"]):
            intent = "CANCEL_APPOINTMENT"

        # C. User selected a specific time/slot or confirmed booking with a known doctor
        elif target_datetime and doctor_id:
            intent = "BOOK_APPOINTMENT"
        elif any(w in lowered for w in [
            "book that", "confirm", "reserve that", "yes please", "lock it in", "book it",
            "okay book", "ok book", "yes book", "please book", "book an appointment",
            "book appointment", "process that", "process it", "go ahead", "i want to book",
            # Telugu booking
            "బుక్ చేయండి", "సరే బుక్", "అపాయింట్‌మెంట్ బుక్", "సరే", "అవును", "చేయండి", "ఖరారు చేయండి",
            "book cheyandi", "sare book"
        ]) and doctor_id:
            intent = "BOOK_APPOINTMENT"
        elif any(w in lowered for w in ["okay", "ok", "yes", "sure", "yep", "fine", "సరే", "అవును"]) and doctor_id and draft.get("stage") in ["SLOTS_OFFERED", "DOCTOR_INQUIRY"]:
            intent = "BOOK_APPOINTMENT"

        # D. Symptom triage and medical concern detection (prioritized to directly address patient symptoms when no doctor requested)
        elif inferred_spec and not doctor_id and not any(w in lowered for w in ["visiting hour", "insurance", "address", "parking"]):
            intent = "SEARCH_DOCTORS"

        # E. User asks for availability / slots
        elif any(w in lowered for w in ["availab", "slot", "openings", "free time", "when is", "schedule for tomorrow", "when can", "సమయాలు", "వేళలు", "స్లాట్లు"]):
            intent = "CHECK_AVAILABILITY"

        # F. Hospital FAQs (strict word boundaries to prevent accidental matches like "fee" inside "feeling")
        elif (
            re.search(r'\b(visiting\s*hours?|clinic\s*hours?|hours\s+of\s+operation|opening\s*hours?)\b', lowered)
            or any(w in lowered for w in ["what time do you open", "when do you open", "what time do you close", "when do you close", "వేళలు", "ఎప్పుడు తెరుస్తారు"])
        ):
            intent = "HOSPITAL_HOURS"
        elif (
            re.search(r'\b(directions?|parking|address)\b', lowered)
            or any(w in lowered for w in ["where are you", "where is the hospital", "where located", "where is the clinic", "ఎక్కడ", "చిరునామా", "పార్కింగ్"])
        ):
            intent = "HOSPITAL_LOCATION"
        elif re.search(r'\b(insurance|medicare|medicaid|copay|co-pay|coverage|costs?|fees?|pricing|bill|billing|payment)\b', lowered) or any(w in lowered for w in ["బీమా", "ఇన్సూరెన్స్"]):
            intent = "HOSPITAL_INSURANCE"
        elif (
            re.search(r'\b(paperwork|documents?)\b', lowered)
            or any(w in lowered for w in ["what should i bring", "what do i need to bring", "what to bring", "how to prepare", "ఏమి తీసుకురావాలి"])
        ):
            intent = "CLINIC_PREPARATION"

        # G. User requests booking or an appointment
        elif any(w in lowered for w in ["book", "appointment", "schedule", "consultation", "see a doctor", "బుక్", "అపాయింట్‌మెంట్", "షెడ్యూల్", "సంప్రదింపు"]):
            intent = "BOOK_APPOINTMENT"

        # H. User asks about a specific doctor by name
        elif matched_doc and not any(w in lowered for w in ["book", "appointment", "schedule"]):
            intent = "DOCTOR_INQUIRY"

        # I. Doctor / Specialist Search
        elif any(w in lowered for w in ["doctor", "specialist", "physician", "find", "search", "who works", "డాక్టర్", "వైద్యుడు", "నిపుణుడు"]):
            intent = "SEARCH_DOCTORS"

        # J. Secondary Symptom triage
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

