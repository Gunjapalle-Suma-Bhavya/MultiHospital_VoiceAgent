"""
AI Real-Time Voice Pipeline, Telephony & Strategy Blueprint Router.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.telephony.inbound_service import TelephonyInboundService
from app.agent.patient_access_agent import PatientAccessAgentService

router = APIRouter(prefix="", tags=["AI Voice & Telephony"])


class VoiceTurnInput(BaseModel):
    patient_phone: str = "+15551234567"
    user_utterance: str
    hospital_id: Optional[str] = None
    session_id: Optional[str] = None

class InboundCallInput(BaseModel):
    caller_phone_number: str

class TelephonyTurnInput(BaseModel):
    session_id: str
    caller_phone_number: str
    speech_text: str
    hospital_id: Optional[str] = None


@router.post("/api/voice/chat")
def voice_agent_chat_endpoint(payload: VoiceTurnInput, db: Session = Depends(get_db)):
    agent_svc = PatientAccessAgentService(db)
    res = agent_svc.process_patient_turn(
        patient_phone=payload.patient_phone,
        user_utterance=payload.user_utterance,
        hospital_id=payload.hospital_id,
        session_id=payload.session_id
    )
    return res

@router.post("/api/v1/telephony/inbound-call")
def telephony_inbound_call(payload: InboundCallInput, db: Session = Depends(get_db)):
    svc = TelephonyInboundService(db)
    return svc.handle_inbound_call(payload.caller_phone_number)

@router.post("/api/v1/telephony/process-turn")
def telephony_process_turn(payload: TelephonyTurnInput, db: Session = Depends(get_db)):
    svc = TelephonyInboundService(db)
    return svc.process_telephony_turn(
        session_id=payload.session_id,
        caller_phone_number=payload.caller_phone_number,
        speech_text=payload.speech_text,
        hospital_id=payload.hospital_id
    )

@router.post("/api/v1/telephony/escalate")
def telephony_escalate(session_id: str, db: Session = Depends(get_db)):
    svc = TelephonyInboundService(db)
    return svc.terminate_call(session_id=session_id, reason="ESCALATED_TO_HUMAN")
