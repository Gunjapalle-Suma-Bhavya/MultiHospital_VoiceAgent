"""
Telephony Integration Service (Section 5.11).

Handles inbound phone interactions:
1. Caller identification & Patient lookup by phone number
2. Phone-driven booking, rescheduling, and cancellation
3. Call termination
4. Automated Human Escalation fallback on AI turn failures
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models import PatientProfile, Appointment
from app.patients.patient_service import PatientSelfServiceService
from app.agent.patient_access_agent import AIPatientAccessAgent


class TelephonyInboundService:
    """
    Inbound phone call lifecycle and escalation manager.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.patient_service = PatientSelfServiceService(db_session)
        self.agent = AIPatientAccessAgent(db_session)

    def handle_inbound_call(self, caller_phone_number: str) -> Dict[str, Any]:
        """
        Triggered when a patient dials into the hospital phone line.
        """
        session_id = str(uuid.uuid4())
        patient = self.patient_service.register_or_update_patient(phone_number=caller_phone_number)

        greeting = (
            f"Thank you for calling our hospital network. Hello {patient.full_name or 'Patient'}! "
            "I am your automated AI voice assistant. How can I assist with your appointments today?"
        )

        return {
            "status": "CALL_CONNECTED",
            "session_id": session_id,
            "caller_phone": caller_phone_number,
            "patient_id": patient.id,
            "greeting_text": greeting,
            "is_known_patient": bool(patient.full_name)
        }

    def process_telephony_turn(
        self,
        session_id: str,
        caller_phone_number: str,
        speech_text: str,
        hospital_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a phone turn via AIPatientAccessAgent. On failure, triggers human escalation.
        """
        try:
            res = self.agent.process_patient_turn(
                channel="telephone",
                patient_identifier=caller_phone_number,
                user_utterance=speech_text,
                session_id=session_id,
                hospital_id=hospital_id
            )

            if res.get("escalation_triggered"):
                res["telephony_action"] = "TRANSFER_TO_HUMAN_OPERATOR"

            return res

        except Exception as e:
            # Fallback path: AI Agent -> Escalation Required -> Human Support
            esc_ticket = str(uuid.uuid4())[:8]
            return {
                "status": "AI_FAILURE_ESCALATED",
                "session_id": session_id,
                "caller_phone": caller_phone_number,
                "speech_response": "I am experiencing technical difficulty. Transferring your call to human support now.",
                "telephony_action": "TRANSFER_TO_HUMAN_OPERATOR",
                "escalation_ticket_id": esc_ticket,
                "error_detail": str(e)
            }

    def terminate_call(self, session_id: str, reason: str = "COMPLETED") -> Dict[str, Any]:
        return {
            "status": "CALL_TERMINATED",
            "session_id": session_id,
            "reason": reason,
            "terminated_at": datetime.utcnow().isoformat()
        }
