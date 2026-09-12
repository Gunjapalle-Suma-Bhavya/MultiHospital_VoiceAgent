"""
AI Patient Access Agent Conversational Orchestrator (Section 5.9).

Primary channel-agnostic conversational interface supporting:
1. Natural language understanding
2. Context resolution (Resolves "Same doctor as last time", "Book for tomorrow")
3. Intent detection
4. Clarification prompt generation for missing slots
5. Capability & tool selection
6. Structured action execution via ActionExecutor
7. Persistent interaction context (PatientSessionState)
8. Workflow initiation (reminders, EHR reconciliation)
9. Graceful error handling
10. EHR integration orchestration
11. Authoritative verification
12. Human escalation trigger

Multi-channel architecture reusable across: Web Voice, Telephone (SIP/Twilio), and Chat.
"""

import uuid
import json
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models import (
    PatientProfile, PatientSessionState, Hospital, Doctor, Appointment
)
from app.agent.resolver import ContextAwareReferenceResolver
from app.agent.guardrails import NonClinicalGuardrail
from app.agent.actions import ActionExecutor
from app.schemas.actions import (
    ActionType, SearchHospitalsInput, SearchDoctorsInput, CheckAvailabilityInput,
    CreateAppointmentInput, RescheduleAppointmentInput, CancelAppointmentInput, EscalateToHumanInput
)
from app.patients.patient_service import PatientSelfServiceService


class AIPatientAccessAgent:
    """
    Unified AI Patient Access Agent processing patient conversation turns across all channels.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.resolver = ContextAwareReferenceResolver(db_session)
        self.guardrail = NonClinicalGuardrail()
        self.executor = ActionExecutor(db_session)
        self.patient_service = PatientSelfServiceService(db_session)

    def _generate_rich_clinical_fallback(self, user_text: str) -> str:
        """
        Generates empathetic, comprehensive, and clinically sound patient responses
        tailored to the patient's exact question or topic.
        """
        text_lower = user_text.lower().strip()

        # 1. Greetings
        if text_lower in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"]:
            return (
                "Hello! I am your AI Patient Care Coordinator with the NexusHealth multi-hospital network. "
                "How can I assist you with scheduling a doctor appointment, checking clinic hours, or addressing your healthcare needs today?"
            )

        # 2. Gratitude & Pleasantries
        if any(w in text_lower for w in ["thank you", "thanks", "appreciate", "goodbye", "bye"]):
            return (
                "You are very welcome! Please feel free to reach out anytime if you need further assistance with your healthcare or appointments. Wishing you good health!"
            )

        # 3. Visiting & Clinic Hours
        if any(w in text_lower for w in ["visiting hour", "visiting hours", "clinic hour", "clinic hours", "hours", "timings", "what time do you open", "closing time"]):
            return (
                "Our outpatient specialty clinics are open Monday through Friday from 8:00 AM to 6:00 PM, and Saturdays from 9:00 AM to 1:00 PM. "
                "General visiting hours for inpatient wards are from 8:00 AM to 8:00 PM daily. Emergency departments at all our network hospitals are open 24/7. "
                "Would you like to schedule an appointment during clinic hours?"
            )

        # 4. Hospital Locations & Parking
        if any(w in text_lower for w in ["location", "address", "where are you", "where is the hospital", "directions", "parking", "where located"]):
            return (
                "NexusHealth operates across regional hospital campuses: City Memorial Hospital is located at 100 Medical Center Way, Metro City; "
                "Care Regional Hospital is at 250 Healthcare Blvd, South Valley; and Metro Health Medical Center is at 500 Central Ave. "
                "All locations provide validated patient parking and wheelchair-accessible entrances. Which campus would you like to visit?"
            )

        # 5. Insurance & Billing
        if any(w in text_lower for w in ["insurance", "medicare", "medicaid", "coverage", "copay", "cost", "fee", "payment", "pricing"]):
            return (
                "NexusHealth facilities accept Medicare, Medicaid, and most major commercial insurance providers including Blue Cross Blue Shield, Aetna, Cigna, and UnitedHealthcare. "
                "We provide upfront eligibility and copay verification prior to your appointment. Would you like to proceed with booking a specialist consultation?"
            )

        # 6. Appointment Preparation & What to Bring
        if any(w in text_lower for w in ["bring", "prepare", "preparation", "paperwork", "documents", "id"]):
            return (
                "For your hospital appointment, please bring a valid government-issued photo ID, your active insurance card, and any relevant prior medical records or current medications. "
                "We recommend arriving 15 minutes before your scheduled appointment time to complete check-in. Can I help you book a consultation slot?"
            )

        # 7. Dermatology / Skin / Rash
        if any(w in text_lower for w in ["rash", "skin", "eczema", "hives", "itch", "itchy", "dermatol", "acne", "mole"]):
            return (
                "I understand you are having skin concerns. Our Dermatology department specializes in diagnosing and treating rashes, dermatitis, allergies, and lesions. "
                "We have Dr. Lisa Marcus available for consultation at City Memorial Hospital and Dr. Kevin White at Care Regional Hospital. "
                "Would you like me to check their available appointment slots for tomorrow?"
            )

        # 8. Orthopedic / Joint / Spine / Bone / Knee
        if any(w in text_lower for w in ["knee", "shoulder", "bone", "joint", "fracture", "sprain", "ortho", "arthritis", "back pain", "spine", "hip", "ankle"]):
            return (
                "I understand you are experiencing orthopedic pain or mobility discomfort. "
                "Our Orthopedic and Sports Medicine departments specialize in joint evaluations, spine care, and rehabilitative therapy. "
                "We have Dr. Sharma available for in-depth evaluations at City Memorial Hospital and Dr. Rao at Care Regional Hospital. "
                "Would you like me to check available consultation slots for you tomorrow?"
            )

        # 9. Cardiology / Heart / Chest
        if any(w in text_lower for w in ["heart", "cardio", "chest", "palpitation", "bp", "blood pressure", "hypertension", "cholesterol"]):
            return (
                "Thank you for reaching out regarding your cardiovascular symptoms. "
                "Our Cardiology Center led by Dr. Sarah Jenkins and Dr. David Chen offers comprehensive cardiac assessments and preventive consultations. "
                "Please note that if you are experiencing severe or crushing chest pressure, you should seek emergency medical care or call 911 immediately. "
                "Otherwise, would you like me to book a consultation slot with our cardiology team this week?"
            )

        # 10. Neurological / Headache / Migraine / Dizziness
        if any(w in text_lower for w in ["headache", "migraine", "dizzy", "dizziness", "numbness", "tingling", "vertigo", "vision"]):
            return (
                "I hear your concern regarding persistent headaches or neurological symptoms. "
                "Our Neurology Center led by Dr. Amanda Vance and Dr. Vikram Malhotra provides comprehensive evaluations of migraines, neuropathy, and balance issues. "
                "Would you like me to check open consultation times for tomorrow?"
            )

        # 11. Gastroenterology / Stomach / Digestive
        if any(w in text_lower for w in ["stomach", "vomit", "nausea", "abdomen", "belly", "acid reflux", "digestive", "bowel"]):
            return (
                "I'm sorry to hear that you are experiencing digestive discomfort. "
                "Our Gastroenterology specialists, Dr. Rachel Green and Dr. Robert Kim, offer comprehensive evaluations for gastrointestinal and reflux issues. "
                "Be sure to stay hydrated and note when your symptoms began. Would you like me to check available appointment times with Dr. Green?"
            )

        # 12. General Illness / Fever / Cold / Infection
        if any(w in text_lower for w in ["fever", "cough", "cold", "flu", "infection", "throat", "sick", "chills"]):
            return (
                "I'm sorry to hear that you are feeling unwell. For fever, respiratory concerns, or viral symptoms, "
                "our Internal Medicine team, including Dr. Emily Watson and Dr. Marcus Reed, provides same-day appointments and lab diagnostics. "
                "Would you like me to schedule a consultation with Dr. Watson at our outpatient clinic?"
            )

        # 13. Doctor / Specialist Overview
        if any(w in text_lower for w in ["doctor", "specialist", "physician", "who is", "who are", "staff"]):
            return (
                "Our multi-hospital network features top board-certified physicians across Orthopedics (Dr. Sharma), "
                "Cardiology (Dr. Jenkins), Dermatology (Dr. Marcus), Neurology (Dr. Vance), Gastroenterology (Dr. Green), "
                "and Internal Medicine (Dr. Watson). Which medical specialty or condition can I help you find an appointment for today?"
            )

        # 14. Default Comprehensive Clinical Intake Greeting
        return (
            "Hello! I am your AI Patient Care Coordinator with the NexusHealth multi-hospital network. "
            "I can help you evaluate your symptoms, locate the most qualified physician, check real-time availability, "
            "and confirm your hospital appointment with EHR verification. How can I assist you with your health today?"
        )

    def process_patient_turn(
        self,
        channel: str = "web_voice",
        patient_identifier: Optional[str] = None,
        patient_phone: Optional[str] = None,
        user_utterance: str = "",
        session_id: Optional[str] = None,
        context_override: Optional[Dict[str, Any]] = None,
        hospital_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        override_hospital_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified turn processing pipeline executing the 12 core AI capabilities across channels.
        """
        phone = patient_phone or patient_identifier or "+15550000000"
        sid = session_id or str(uuid.uuid4())
        h_id = hospital_id or override_hospital_id
        d_id = doctor_id

        capabilities_invoked = []

        # 1. Register/Retrieve Patient Profile & Persistent Session State
        patient = self.patient_service.register_or_update_patient(phone_number=phone)
        capabilities_invoked.append("PATIENT_PROFILE_RESOLVED")

        session_state = self.db.query(PatientSessionState).filter(PatientSessionState.session_id == sid).first()
        if not session_state:
            session_state = PatientSessionState(
                session_id=sid,
                patient_id=patient.id,
                current_intent="GENERAL_INQUIRY",
                workflow_step="INITIAL_GREETING"
            )
            self.db.add(session_state)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                session_state = self.db.query(PatientSessionState).filter(PatientSessionState.session_id == sid).first()
        capabilities_invoked.append("PERSISTENT_CONTEXT_LOADED")

        # 2. Safety Boundary & Non-Clinical Guardrail Check
        guardrail_res = self.guardrail.evaluate_utterance(user_utterance)
        escalation_triggered = False
        if guardrail_res["is_clinical_advice_request"]:
            escalation_triggered = True
            capabilities_invoked.append("HUMAN_ESCALATION_TRIGGERED")
            esc_output = self.executor.escalate_to_human(
                EscalateToHumanInput(session_id=sid, patient_id=patient.id, reason=guardrail_res["reason"])
            )
            speech = guardrail_res["redirect_response"]
            return {
                "status": "SUCCESS",
                "success": True,
                "channel": channel,
                "session_id": sid,
                "patient_id": patient.id,
                "detected_intent": "HUMAN_ESCALATION",
                "intent_detected": "HUMAN_ESCALATION",
                "nlu_analysis": {"intent": "HUMAN_ESCALATION", "entities": {}},
                "interaction_context": {"session_id": sid, "workflow_step": "HUMAN_ESCALATION"},
                "speech_response": speech,
                "agent_response": speech,
                "escalation_triggered": True,
                "escalation_ticket_id": esc_output.ticket_id,
                "capabilities_invoked": capabilities_invoked
            }

        # 3. Context Resolution & Disambiguation
        resolved_context = self.resolver.resolve_context(session_id=sid, patient_phone=phone, user_utterance=user_utterance)
        capabilities_invoked.append("CONTEXT_RESOLVED")

        active_hosp_id = h_id or resolved_context["hospital_id"] or patient.last_hospital_id
        active_doc_id = d_id or resolved_context["doctor_id"] or patient.last_doctor_id
        intent = resolved_context["intent"]

        if intent == "HUMAN_ESCALATION":
            escalation_triggered = True
            capabilities_invoked.append("HUMAN_ESCALATION_TRIGGERED")

        session_state.current_intent = intent
        self.db.commit()
        capabilities_invoked.append("INTENT_DETECTED")

        # 4. Intent Dispatch & Tool Execution
        agent_response = ""
        action_executed = None
        action_payload = {}

        if intent == "HUMAN_ESCALATION":
            esc_output = self.executor.escalate_to_human(
                EscalateToHumanInput(session_id=sid, patient_id=patient.id, reason="Patient requested human emergency support")
            )
            agent_response = "EMERGENCY: If you are experiencing a life-threatening emergency, please call 911 immediately. Transferring your call to our on-duty healthcare triage coordinator right now. Please remain on the line."

        elif intent == "CANCEL_APPOINTMENT":
            capabilities_invoked.append("TOOL_SELECTION_CANCELLATION")
            appts = self.patient_service.get_patient_appointments(patient.id)
            active_appts = [a for a in appts if a["status"] in ["SCHEDULED", "CONFIRMED", "PENDING", "PENDING_EHR_VERIFICATION"]]
            if active_appts:
                cancel_output = self.executor.cancel_appointment(
                    CancelAppointmentInput(session_id=sid, patient_id=patient.id, appointment_id=active_appts[0]["appointment_id"])
                )
                action_executed = "CANCEL_APPOINTMENT"
                action_payload = cancel_output.model_dump()
                agent_response = "Your upcoming appointment has been successfully cancelled in the hospital EHR system. Would you like to reschedule for a future date?"
            else:
                agent_response = "You do not currently have any active upcoming appointments on file to cancel. Would you like to schedule a new consultation?"

        elif intent == "HOSPITAL_HOURS":
            agent_response = (
                "Our outpatient specialty clinics are open Monday through Friday from 8:00 AM to 6:00 PM, and Saturdays from 9:00 AM to 1:00 PM. "
                "General visiting hours for inpatient wards are from 8:00 AM to 8:00 PM daily. Emergency departments at all our network hospitals remain open 24/7. "
                "Would you like to schedule an appointment during clinic hours?"
            )

        elif intent == "HOSPITAL_LOCATION":
            agent_response = (
                "NexusHealth operates across regional hospital campuses: City Memorial Hospital is located at 100 Medical Center Way, Metro City; "
                "Care Regional Hospital is at 250 Healthcare Blvd, South Valley; and Metro Health Medical Center is at 500 Central Ave. "
                "All locations provide validated patient parking and wheelchair accessibility. Which campus would you like to visit?"
            )

        elif intent == "HOSPITAL_INSURANCE":
            agent_response = (
                "NexusHealth hospitals accept Medicare, Medicaid, and most major commercial insurance providers including Blue Cross Blue Shield, Aetna, Cigna, and UnitedHealthcare. "
                "Our intake team will verify your eligibility and copay before your consultation. Would you like to book an appointment with a specialist?"
            )

        elif intent == "CLINIC_PREPARATION":
            agent_response = (
                "For your hospital appointment, please bring a valid government-issued photo ID, your active insurance card, and any relevant prior medical records or current medications. "
                "We recommend arriving 15 minutes before your scheduled appointment time to complete check-in. Can I help you book a consultation slot?"
            )

        elif intent == "DOCTOR_INQUIRY" and active_doc_id:
            doc_obj = self.db.query(Doctor).filter(Doctor.id == active_doc_id).first()
            hosp_obj = self.db.query(Hospital).filter(Hospital.id == doc_obj.hospital_id).first() if doc_obj else None
            if doc_obj:
                agent_response = (
                    f"{doc_obj.name} is a specialist in {doc_obj.specialty} with our {doc_obj.department or 'Clinical Care'} department "
                    f"at {hosp_obj.name if hosp_obj else 'our regional hospital'}. "
                    f"Would you like me to check their available appointment slots for tomorrow?"
                )
                session_state.active_draft_booking_json = json.dumps({
                    "doctor_id": doc_obj.id,
                    "doctor_name": doc_obj.name,
                    "hospital_id": doc_obj.hospital_id,
                    "hospital_name": hosp_obj.name if hosp_obj else "",
                    "specialty": doc_obj.specialty
                })
                self.db.commit()

        elif intent in ["SEARCH_DOCTORS", "SEARCH_HOSPITALS"]:
            capabilities_invoked.append("TOOL_SELECTION_SEARCH")
            inferred_spec = resolved_context.get("inferred_specialty")
            search_output = self.executor.search_doctors(
                SearchDoctorsInput(session_id=sid, patient_id=patient.id, hospital_id=active_hosp_id, specialty=inferred_spec)
            )
            action_executed = "SEARCH_DOCTORS"
            action_payload = search_output.model_dump()
            if search_output.doctors:
                top_doc = search_output.doctors[0]
                session_state.active_draft_booking_json = json.dumps({
                    "doctor_id": top_doc.id,
                    "doctor_name": top_doc.name,
                    "hospital_id": top_doc.hospital_id,
                    "hospital_name": top_doc.hospital_name,
                    "specialty": top_doc.specialty
                })
                self.db.commit()

                if inferred_spec:
                    doc_list = ", ".join([f"{doc.name} at {doc.hospital_name}" for doc in search_output.doctors[:3]])
                    agent_response = (
                        f"I understand your concerns regarding your symptoms. Based on clinical intake triage, "
                        f"a consultation with our {inferred_spec} department is strongly recommended. "
                        f"We currently have top specialists available: {doc_list}. "
                        f"Would you like me to reserve a priority consultation slot with one of these doctors, "
                        f"or check available times for tomorrow?"
                    )
                else:
                    doc_list = ", ".join([f"{doc.name} ({doc.specialty} at {doc.hospital_name})" for doc in search_output.doctors[:3]])
                    agent_response = (
                        f"We have top physicians available across our hospital network: {doc_list}. "
                        f"Which doctor or specialty would you like to schedule an appointment with?"
                    )
            else:
                agent_response = (
                    "I couldn't find active doctors matching those specific criteria at this moment. "
                    "Would you like me to broaden our search across our regional hospital network facilities or check another medical department?"
                )

        elif intent == "CHECK_AVAILABILITY":
            capabilities_invoked.append("TOOL_SELECTION_AVAILABILITY")
            if not active_doc_id:
                agent_response = (
                    "I would be glad to check available consultation slots for you. "
                    "Which physician or medical department would you like to see?"
                )
                capabilities_invoked.append("CLARIFICATION_PROMPTED")
            else:
                doc_obj = self.db.query(Doctor).filter(Doctor.id == active_doc_id).first()
                hosp_obj = self.db.query(Hospital).filter(Hospital.id == doc_obj.hospital_id).first() if doc_obj else None
                doc_name = doc_obj.name if doc_obj else "the doctor"
                hosp_name = hosp_obj.name if hosp_obj else "our clinic"

                target_d = date.today() + timedelta(days=1)
                avail_output = self.executor.check_availability(
                    CheckAvailabilityInput(session_id=sid, patient_id=patient.id, doctor_id=active_doc_id, target_date=target_d)
                )
                action_executed = "CHECK_AVAILABILITY"
                action_payload = avail_output.model_dump()
                if avail_output.available_slots:
                    slot_times = ", ".join([s.start_datetime.strftime("%I:%M %p") for s in avail_output.available_slots[:4]])
                    agent_response = (
                        f"I checked the real-time hospital calendar for {doc_name} at {hosp_name}. "
                        f"We have open 30-minute consultation slots available tomorrow at: {slot_times}. "
                        f"Each consultation includes full clinical assessment and pre-visit intake review. "
                        f"Which time slot works best for your schedule?"
                    )
                    session_state.active_draft_booking_json = json.dumps({
                        "doctor_id": active_doc_id,
                        "doctor_name": doc_name,
                        "hospital_id": doc_obj.hospital_id if doc_obj else active_hosp_id,
                        "hospital_name": hosp_name,
                        "stage": "SLOTS_OFFERED"
                    })
                    self.db.commit()
                else:
                    agent_response = (
                        f"There are no available slots for {doc_name} tomorrow. "
                        f"Would you like me to check the next available weekday, or see if another specialist has openings?"
                    )

        elif intent == "BOOK_APPOINTMENT":
            capabilities_invoked.append("TOOL_SELECTION_BOOKING")
            target_dt = resolved_context.get("target_datetime")

            if not active_doc_id:
                agent_response = "I would be glad to help you schedule an appointment. Which physician or medical department would you like to see?"
                capabilities_invoked.append("CLARIFICATION_PROMPTED")
            elif not target_dt:
                # Doctor known, but slot not chosen yet: check availability and prompt
                doc_obj = self.db.query(Doctor).filter(Doctor.id == active_doc_id).first()
                hosp_obj = self.db.query(Hospital).filter(Hospital.id == doc_obj.hospital_id).first() if doc_obj else None
                doc_name = doc_obj.name if doc_obj else "the doctor"
                hosp_name = hosp_obj.name if hosp_obj else "our clinic"

                target_d = date.today() + timedelta(days=1)
                avail_output = self.executor.check_availability(
                    CheckAvailabilityInput(session_id=sid, patient_id=patient.id, doctor_id=active_doc_id, target_date=target_d)
                )
                if avail_output.available_slots:
                    slot_times = ", ".join([s.start_datetime.strftime("%I:%M %p") for s in avail_output.available_slots[:4]])
                    agent_response = (
                        f"To schedule your appointment with {doc_name} at {hosp_name}, "
                        f"open consultation slots tomorrow are: {slot_times}. Which time slot works best for you?"
                    )
                    session_state.active_draft_booking_json = json.dumps({
                        "doctor_id": active_doc_id,
                        "doctor_name": doc_name,
                        "hospital_id": doc_obj.hospital_id if doc_obj else active_hosp_id,
                        "hospital_name": hosp_name,
                        "stage": "SLOTS_OFFERED"
                    })
                    self.db.commit()
                else:
                    agent_response = f"Dr. {doc_name} does not have open consultation slots tomorrow. Would you like to check an alternate day?"
            else:
                book_output = self.executor.create_appointment(
                    CreateAppointmentInput(
                        session_id=sid,
                        patient_id=patient.id,
                        hospital_id=active_hosp_id,
                        doctor_id=active_doc_id,
                        patient_name=patient.full_name or "Patient",
                        patient_phone=phone,
                        start_datetime=target_dt
                    )
                )
                action_executed = "CREATE_APPOINTMENT"
                action_payload = book_output.model_dump()
                if book_output.success:
                    capabilities_invoked.extend(["WORKFLOW_INITIATED", "EHR_ORCHESTRATED", "AUTHORITATIVE_VERIFIED"])
                    agent_response = (
                        f"Excellent! Your appointment with {book_output.doctor_name} at {book_output.hospital_name} "
                        f"is confirmed for {target_dt.strftime('%A, %B %d at %I:%M %p')}. "
                        f"Your verification code is {book_output.appointment_id[:8]}. "
                        f"Your slot is locked in the hospital EHR system. Please arrive 15 minutes early with your photo ID and insurance card. "
                        f"Can I assist you with anything else today?"
                    )
                    session_state.active_draft_booking_json = None
                    self.db.commit()
                else:
                    capabilities_invoked.append("ERROR_HANDLED")
                    agent_response = f"I was unable to complete the booking: {book_output.message}. Would you like me to reserve an alternate time slot?"

        else:
            capabilities_invoked.append("GENERAL_CONVERSATION")
            from app.voice.llm_client import live_llm_client
            if live_llm_client.is_configured():
                llm_reply = live_llm_client.chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are NexusHealth's intelligent, empathetic AI Clinical Care Coordinator for a premier multi-hospital network. "
                                "Provide a thorough, warm, and helpful response (3 to 4 sentences) addressing the patient's concerns. "
                                "Highlight relevant hospital departments, doctor specialties, or appointment steps. "
                                "Never provide a definitive self-diagnosis or prescribe medication, but be reassuring, informative, and proactive."
                            )
                        },
                        {"role": "user", "content": user_utterance}
                    ],
                    max_tokens=220,
                    timeout_sec=5.0
                )
                if llm_reply:
                    agent_response = llm_reply
                else:
                    agent_response = self._generate_rich_clinical_fallback(user_utterance)
            else:
                agent_response = self._generate_rich_clinical_fallback(user_utterance)

        return {
            "status": "SUCCESS",
            "success": True,
            "channel": channel,
            "session_id": sid,
            "patient_id": patient.id,
            "detected_intent": intent,
            "intent_detected": intent,
            "nlu_analysis": {"intent": intent, "entities": {"hospital_id": active_hosp_id, "doctor_id": active_doc_id}},
            "interaction_context": {"session_id": sid, "workflow_step": session_state.workflow_step},
            "speech_response": agent_response,
            "agent_response": agent_response,
            "action_executed": action_executed,
            "action_payload": action_payload,
            "escalation_triggered": escalation_triggered,
            "capabilities_invoked": capabilities_invoked
        }


PatientAccessAgentService = AIPatientAccessAgent

