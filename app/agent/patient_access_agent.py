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
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

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
            self.db.commit()
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

        if intent in ["SEARCH_HOSPITALS", "SEARCH_DOCTORS"] and not active_doc_id:
            capabilities_invoked.append("TOOL_SELECTION_SEARCH")
            search_output = self.executor.search_doctors(
                SearchDoctorsInput(session_id=sid, patient_id=patient.id, hospital_id=active_hosp_id)
            )
            action_executed = "SEARCH_DOCTORS"
            action_payload = search_output.model_dump()
            if search_output.doctors:
                doc_list = ", ".join([f"{doc.name} ({doc.specialty})" for doc in search_output.doctors[:3]])
                agent_response = f"I found available doctors: {doc_list}. Which doctor would you like to schedule with?"
            else:
                agent_response = "I couldn't find active doctors matching your criteria. Would you like to check another specialty?"

        elif intent == "CHECK_AVAILABILITY" or (intent == "BOOK_APPOINTMENT" and not resolved_context.get("target_datetime")):
            capabilities_invoked.append("TOOL_SELECTION_AVAILABILITY")
            if not active_doc_id:
                agent_response = "I would be glad to check available slots for you. Which doctor or specialty would you like to see?"
                capabilities_invoked.append("CLARIFICATION_PROMPTED")
            else:
                target_d = date.today() + timedelta(days=1)
                avail_output = self.executor.check_availability(
                    CheckAvailabilityInput(session_id=sid, patient_id=patient.id, doctor_id=active_doc_id, target_date=target_d)
                )
                action_executed = "CHECK_AVAILABILITY"
                action_payload = avail_output.model_dump()
                if avail_output.available_slots:
                    slot_times = ", ".join([s.start_datetime.strftime("%I:%M %p") for s in avail_output.available_slots[:3]])
                    agent_response = f"Doctor is available tomorrow at: {slot_times}. Which time works best for you?"
                else:
                    agent_response = "There are no available slots for that date. Would you like me to search another day?"

        elif intent == "BOOK_APPOINTMENT":
            capabilities_invoked.append("TOOL_SELECTION_BOOKING")
            if not active_doc_id or not active_hosp_id:
                agent_response = "To book your appointment, please specify the doctor and hospital you would like to visit."
                capabilities_invoked.append("CLARIFICATION_PROMPTED")
            else:
                target_dt = resolved_context.get("target_datetime") or (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, hours=10))
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
                    agent_response = f"Your appointment with {book_output.doctor_name} at {book_output.hospital_name} is confirmed for {target_dt.strftime('%B %d at %I:%M %p')}. Confirmation ID: {book_output.appointment_id[:8]}."
                else:
                    capabilities_invoked.append("ERROR_HANDLED")
                    agent_response = f"I was unable to complete the booking: {book_output.message}. Would you like to select a different time?"

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
                agent_response = "Your upcoming appointment has been successfully cancelled."
            else:
                agent_response = "You do not have any active upcoming appointments to cancel."

        elif intent == "HUMAN_ESCALATION":
            esc_output = self.executor.escalate_to_human(
                EscalateToHumanInput(session_id=sid, patient_id=patient.id, reason="Patient requested human emergency support")
            )
            agent_response = "EMERGENCY: Transferring your call to a human healthcare specialist immediately."

        else:
            capabilities_invoked.append("GENERAL_CONVERSATION")
            agent_response = f"Hello! I am your AI Patient Access Assistant. How can I help you schedule or manage doctor appointments today?"

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

